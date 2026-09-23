"""KiranaFlow AI - AI Provider Abstraction

Configurable AI provider that can be swapped via environment variables.
Supports: Gemini, OpenAI, Ollama, and a built-in Mock provider.
"""

import json
import re
import logging
from abc import ABC, abstractmethod
from typing import Optional
from ..config import settings
from .language_rules import (
    canonicalize_text, extract_qty_unit_product, is_repeat_request,
)

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def parse_customer_request(self, message: str) -> dict:
        """
        Parse a natural-language customer request into structured data.
        Returns: {"intent": str, "items": [{"product_query": str, "quantity": int}], "delivery": bool}
        """
        pass


class MockAIProvider(AIProvider):
    """
    Built-in rule-based parser for natural language kirana orders.
    Works without any external API. Handles Hindi, Hinglish, and English.
    """

    # Hindi/Hinglish number words
    NUMBER_WORDS = {
        "ek": 1, "एक": 1, "one": 1,
        "do": 2, "दो": 2, "two": 2,
        "teen": 3, "तीन": 3, "three": 3,
        "char": 4, "चार": 4, "four": 4,
        "paanch": 5, "panch": 5, "पांच": 5, "five": 5,
        "cheh": 6, "छह": 6, "six": 6,
        "saat": 7, "सात": 7, "seven": 7,
        "aath": 8, "आठ": 8, "eight": 8,
        "nau": 9, "नौ": 9, "nine": 9,
        "das": 10, "दस": 10, "ten": 10,
        "half": 1, "aadha": 1,
    }

    # Delivery indicators
    DELIVERY_KEYWORDS = [
        "deliver", "bhej", "bhejdo", "bhej do", "bhej dena", "bhejdena",
        "ghar pe", "ghar par", "ghar", "home", "address",
        "ship", "send", "door", "doorstep",
    ]

    # Noise words to strip (units are parsed separately)
    NOISE_WORDS = {
        "bhaiya", "bhai", "didi", "please", "bro", "sir", "madam",
        "chahiye", "chahie", "chaiye", "dena", "de", "do", "dedo",
        "woh", "wala", "wali", "aur", "or", "and", "&",
        "mujhe", "muje", "humko", "hume", "mereko",
        "the", "a", "an", "some", "of",
    }

    def _clean_product_query(self, query: str) -> str:
        """Remove noise words and canonicalize Hinglish → catalog English."""
        query = canonicalize_text(query)
        words = query.split()
        cleaned = [w for w in words if w not in self.NOISE_WORDS and len(w) > 1]
        result = " ".join(cleaned).strip()
        return result if result else query.strip()

    async def parse_customer_request(self, message: str) -> dict:
        """Parse natural language into structured order data."""
        original = message
        if is_repeat_request(message):
            return {
                "intent": "repeat_last_order",
                "items": [],
                "delivery": True,
                "raw_message": original,
            }

        text = canonicalize_text(message)
        delivery = any(kw in text for kw in self.DELIVERY_KEYWORDS)

        for kw in sorted(self.DELIVERY_KEYWORDS, key=len, reverse=True):
            text = text.replace(kw, " ")

        for prefix in ["bhaiya", "bhai", "didi", "please", "mujhe", "humko", "hume", "mereko"]:
            text = re.sub(r"\b" + prefix + r"\b", " ", text)

        segments = re.split(r"\s+aur\s+|\s+or\s+|\s+and\s+|\s*,\s*|\s*&\s*", text)

        items = []
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            qty, unit, product_query = extract_qty_unit_product(segment)
            product_query = self._clean_product_query(product_query)

            if product_query and len(product_query) > 1:
                items.append({
                    "product_query": product_query,
                    "quantity": max(1, qty),
                    "unit": unit,
                })

        return {
            "intent": "create_order" if items else "unknown",
            "items": items,
            "delivery": delivery,
            "raw_message": original,
        }


class GeminiProvider(AIProvider):
    """Google Gemini AI provider (using google-genai SDK)."""

    def __init__(self):
        try:
            from google import genai
            self.client = genai.Client(api_key=settings.gemini_api_key)
            self.model_name = "gemini-2.0-flash"
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    async def parse_customer_request(self, message: str) -> dict:
        prompt = f"""You are a kirana store order parser. Parse this customer message into a JSON order.
The customer speaks in Hindi, Hinglish, or English.

Message: "{message}"

Return ONLY valid JSON (no markdown, no explanation):
{{
  "intent": "create_order",
  "items": [
    {{"product_query": "product name in english", "quantity": number}}
  ],
  "delivery": true/false
}}

Rules:
- The customer speaks Hindi, Hinglish, or English. Treat them equally.
- aata/atta/gehun = atta. doodh = milk. tel = oil. namak = salt. cheeni = sugar. chawal = rice.
- "2 kilo aata" means quantity=2, unit=kg, product_query="atta" (kilo = kg).
- If the brand is missing (just "atta"), still return product_query="atta".
- Keep brand names (Maggi, Amul, Tata, Fortune, Aashirvaad, Patanjali).
- Default quantity to 1 if not specified.
- delivery=true if they mention home delivery, "bhej do", "ghar pe", etc.
- If they say "pichla order" / "repeat last order", set intent to "repeat_last_order".
- Return items as: {{"product_query": "...", "quantity": N, "unit": "kg"|"l"|"pack"|""}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            text = response.text.strip()
            # Extract JSON from possible markdown
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            result = json.loads(text)
            result["raw_message"] = message
            return result
        except Exception as e:
            logger.error(f"Gemini parsing error: {e}")
            # Fall back to mock parser
            fallback = MockAIProvider()
            return await fallback.parse_customer_request(message)


class OpenAIProvider(AIProvider):
    """OpenAI provider."""

    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    async def parse_customer_request(self, message: str) -> dict:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a kirana store order parser. Parse customer messages "
                            "(Hindi/Hinglish/English) into JSON orders. Return ONLY valid JSON: "
                            '{"intent":"create_order","items":[{"product_query":"name","quantity":N}],"delivery":bool}'
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(response.choices[0].message.content)
            result["raw_message"] = message
            return result
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
            fallback = MockAIProvider()
            return await fallback.parse_customer_request(message)


def get_ai_provider() -> AIProvider:
    """Factory function to get the configured AI provider."""
    provider = settings.ai_provider.lower()

    if provider == "gemini":
        return GeminiProvider()
    elif provider == "openai":
        return OpenAIProvider()
    elif provider == "mock":
        return MockAIProvider()
    else:
        logger.warning(f"Unknown AI provider '{provider}', falling back to mock")
        return MockAIProvider()
