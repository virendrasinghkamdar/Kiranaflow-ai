"""KiranaFlow AI - Agent API Routes

Primary endpoint for the autonomous order pipeline.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import CustomerRequest, OrderResult
from ..agents.order_agent import OrderAgent

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/process", response_model=OrderResult)
async def process_customer_request(
    request: CustomerRequest,
    db: Session = Depends(get_db),
):
    """
    Process a natural-language customer request through the
    autonomous agent pipeline.

    The agent will:
    1. Parse the request
    2. Identify and resolve products
    3. Check inventory
    4. Retrieve prices
    5. Handle unavailable items
    6. Calculate totals
    7. Create the order
    8. Update inventory
    9. Check low stock
    10. Send confirmation
    """
    agent = OrderAgent(db)
    result = await agent.process_request(
        message=request.message,
        customer_phone=request.customer_phone,
        channel=request.channel,
        selections=[s.model_dump() for s in request.selections],
    )
    return result
