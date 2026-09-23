"""KiranaFlow AI - Database Seed Data

Neighborhood kirana catalog + customer base + historical orders.
Seed is additive: existing rows are kept, missing products/customers are inserted.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from ..models import Product, Customer, DeliveryPerson, Order, OrderItem


def _margin_for(category: str) -> float:
    """Typical kirana margin by category (used to derive CP from SP)."""
    table = {
        "Atta & Flour": 0.12,
        "Cooking Oil": 0.10,
        "Rice & Dal": 0.11,
        "Noodles & Snacks": 0.28,
        "Salt & Spices": 0.22,
        "Dairy": 0.14,
        "Biscuits & Cookies": 0.20,
        "Beverages": 0.18,
        "Essentials": 0.12,
        "Personal Care": 0.16,
        "Household": 0.15,
        "Bread & Breakfast": 0.18,
        "Baby & Kids": 0.16,
    }
    return table.get(category, 0.15)


def _product(**kwargs) -> Product:
    price = float(kwargs.get("price") or 0)
    if "cost_price" not in kwargs:
        kwargs["cost_price"] = round(price * (1 - _margin_for(kwargs.get("category", ""))), 2)
    return Product(**kwargs)


def all_catalog_products():
    return [
        # ── Atta & Flour ──
        _product(name="Aashirvaad Atta", category="Atta & Flour", brand="Aashirvaad", unit="5kg", price=320, stock=45, low_stock_threshold=8,
                 description="Aashirvaad Superior MP Whole Wheat Atta 5kg",
                 aliases=["atta", "aashirvaad", "aashirwad atta", "gehun ka atta", "wheat flour", "aashirvaad atta 5kg"]),
        _product(name="Fortune Chakki Atta", category="Atta & Flour", brand="Fortune", unit="5kg", price=295, stock=30, low_stock_threshold=8,
                 description="Fortune Chakki Fresh Atta 5kg", aliases=["fortune atta", "chakki atta", "fortune chakki"]),
        _product(name="Pillsbury Atta", category="Atta & Flour", brand="Pillsbury", unit="5kg", price=310, stock=22, low_stock_threshold=5,
                 description="Pillsbury Chakki Fresh Atta 5kg", aliases=["pillsbury", "pillsbury atta"]),
        _product(name="Patanjali Atta", category="Atta & Flour", brand="Patanjali", unit="5kg", price=280, stock=0, low_stock_threshold=5,
                 description="Patanjali Whole Wheat Atta 5kg", aliases=["patanjali atta", "patanjali"]),
        _product(name="Aashirvaad Multigrain Atta", category="Atta & Flour", brand="Aashirvaad", unit="5kg", price=370, stock=12, low_stock_threshold=4,
                 description="Aashirvaad Multigrain Atta 5kg", aliases=["multigrain atta", "multigrain"]),
        _product(name="Rajdhani Besan", category="Atta & Flour", brand="Rajdhani", unit="1kg", price=95, stock=18, low_stock_threshold=5,
                 description="Rajdhani Besan (Gram Flour) 1kg", aliases=["besan", "gram flour", "chana atta"]),
        _product(name="Shakti Bhog Atta", category="Atta & Flour", brand="Shakti Bhog", unit="10kg", price=580, stock=16, low_stock_threshold=4,
                 description="Shakti Bhog Chakki Atta 10kg", aliases=["shakti bhog", "shakti atta"]),
        _product(name="Annapurna Atta", category="Atta & Flour", brand="Annapurna", unit="5kg", price=285, stock=14, low_stock_threshold=4,
                 description="Annapurna Atta 5kg", aliases=["annapurna atta", "annapurna"]),
        _product(name="Maida", category="Atta & Flour", brand="Local", unit="1kg", price=42, stock=40, low_stock_threshold=10,
                 description="Refined Wheat Flour (Maida) 1kg", aliases=["maida", "refined flour"]),
        _product(name="Sooji Rava Premium", category="Atta & Flour", brand="Local", unit="1kg", price=55, stock=22, low_stock_threshold=6,
                 description="Premium Sooji / Bombay Rava 1kg", aliases=["sooji rava", "bombay rava"]),

        # ── Cooking Oil ──
        _product(name="Fortune Sunflower Oil", category="Cooking Oil", brand="Fortune", unit="1L", price=145, stock=35, low_stock_threshold=8,
                 description="Fortune Sunlite Refined Sunflower Oil 1L",
                 aliases=["fortune oil", "sunflower oil", "tel", "fortune tel", "oil", "cooking oil"]),
        _product(name="Saffola Gold Oil", category="Cooking Oil", brand="Saffola", unit="1L", price=195, stock=20, low_stock_threshold=5,
                 description="Saffola Gold Blended Edible Vegetable Oil 1L", aliases=["saffola", "saffola oil", "saffola gold"]),
        _product(name="Fortune Mustard Oil", category="Cooking Oil", brand="Fortune", unit="1L", price=180, stock=25, low_stock_threshold=6,
                 description="Fortune Kachi Ghani Pure Mustard Oil 1L", aliases=["mustard oil", "sarson ka tel", "kachi ghani"]),
        _product(name="Fortune Rice Bran Oil", category="Cooking Oil", brand="Fortune", unit="1L", price=160, stock=15, low_stock_threshold=5,
                 description="Fortune Rice Bran Health Oil 1L", aliases=["rice bran oil", "fortune rice bran"]),
        _product(name="Dhara Refined Oil", category="Cooking Oil", brand="Dhara", unit="1L", price=135, stock=28, low_stock_threshold=6,
                 description="Dhara Refined Vegetable Oil 1L", aliases=["dhara oil", "dhara", "vegetable oil"]),
        _product(name="Nature Fresh Ghee", category="Cooking Oil", brand="Nature Fresh", unit="1L", price=550, stock=10, low_stock_threshold=3,
                 description="Nature Fresh Acti-Lite Pure Cow Ghee 1L", aliases=["ghee", "desi ghee", "cow ghee"]),
        _product(name="Fortune Sunflower Oil 5L", category="Cooking Oil", brand="Fortune", unit="5L", price=690, stock=12, low_stock_threshold=3,
                 description="Fortune Sunlite Sunflower Oil 5L Jerry", aliases=["5 litre oil", "fortune 5l", "tel 5 litre"]),
        _product(name="Amul Cow Ghee", category="Cooking Oil", brand="Amul", unit="1L", price=620, stock=9, low_stock_threshold=3,
                 description="Amul Pure Cow Ghee 1L", aliases=["amul ghee", "amul cow ghee"]),
        _product(name="Engine Mustard Oil", category="Cooking Oil", brand="Engine", unit="1L", price=175, stock=18, low_stock_threshold=5,
                 description="Engine Kachi Ghani Mustard Oil 1L", aliases=["engine oil mustard", "engine tel"]),
        _product(name="Parachute Coconut Oil", category="Cooking Oil", brand="Parachute", unit="500ml", price=145, stock=24, low_stock_threshold=6,
                 description="Parachute 100% Pure Coconut Oil 500ml", aliases=["coconut oil", "nariyal tel", "parachute"]),

        # ── Rice & Dal ──
        _product(name="India Gate Basmati Rice", category="Rice & Dal", brand="India Gate", unit="5kg", price=420, stock=30, low_stock_threshold=5,
                 description="India Gate Classic Basmati Rice 5kg", aliases=["rice", "basmati", "chawal", "india gate rice"]),
        _product(name="Daawat Rozana Rice", category="Rice & Dal", brand="Daawat", unit="5kg", price=350, stock=25, low_stock_threshold=5,
                 description="Daawat Rozana Super Basmati Rice 5kg", aliases=["daawat rice", "rozana rice", "daawat"]),
        _product(name="Toor Dal", category="Rice & Dal", brand="Local", unit="1kg", price=155, stock=40, low_stock_threshold=10,
                 description="Premium Toor Dal 1kg", aliases=["dal", "toor dal", "arhar dal", "daal"]),
        _product(name="Moong Dal", category="Rice & Dal", brand="Local", unit="1kg", price=125, stock=35, low_stock_threshold=8,
                 description="Yellow Moong Dal 1kg", aliases=["moong dal", "moong", "moong daal", "yellow dal"]),
        _product(name="Chana Dal", category="Rice & Dal", brand="Local", unit="1kg", price=110, stock=30, low_stock_threshold=8,
                 description="Chana Dal 1kg", aliases=["chana dal", "chana", "chana daal"]),
        _product(name="Rajma", category="Rice & Dal", brand="Local", unit="1kg", price=170, stock=20, low_stock_threshold=5,
                 description="Kashmiri Rajma (Kidney Beans) 1kg", aliases=["rajma", "kidney beans", "rajmah"]),
        _product(name="Kohinoor Super Basmati", category="Rice & Dal", brand="Kohinoor", unit="5kg", price=480, stock=14, low_stock_threshold=4,
                 description="Kohinoor Super Silver Basmati 5kg", aliases=["kohinoor rice", "kohinoor"]),
        _product(name="Lal Qilla Traditional Basmati", category="Rice & Dal", brand="Lal Qilla", unit="5kg", price=510, stock=10, low_stock_threshold=3,
                 description="Lal Qilla Traditional Basmati Rice 5kg", aliases=["lal qilla", "lalquilla"]),
        _product(name="Masoor Dal", category="Rice & Dal", brand="Local", unit="1kg", price=118, stock=28, low_stock_threshold=8,
                 description="Masoor Dal (Red Lentil) 1kg", aliases=["masoor", "masoor dal", "red dal"]),
        _product(name="Urad Dal", category="Rice & Dal", brand="Local", unit="1kg", price=148, stock=22, low_stock_threshold=6,
                 description="Urad Dal Split 1kg", aliases=["urad", "urad dal", "black gram"]),
        _product(name="Kabuli Chana", category="Rice & Dal", brand="Local", unit="1kg", price=132, stock=18, low_stock_threshold=5,
                 description="Kabuli Chana (Chickpeas) 1kg", aliases=["kabuli chana", "chole", "chickpea"]),
        _product(name="Poha Thick", category="Rice & Dal", brand="Local", unit="1kg", price=62, stock=26, low_stock_threshold=8,
                 description="Thick Poha 1kg", aliases=["thick poha"]),

        # ── Noodles & Snacks ──
        _product(name="Maggi 2-Minute Noodles", category="Noodles & Snacks", brand="Maggi", unit="70g", price=14, stock=100, low_stock_threshold=20,
                 description="Maggi 2-Minute Masala Noodles 70g",
                 aliases=["maggi", "noodles", "maggi noodles", "2 minute maggi", "maggi masala"]),
        _product(name="Yippee Noodles", category="Noodles & Snacks", brand="Yippee", unit="70g", price=14, stock=60, low_stock_threshold=15,
                 description="Sunfeast Yippee Magic Masala Noodles 70g", aliases=["yippee", "yippee noodles", "sunfeast noodles"]),
        _product(name="Kurkure Masala Munch", category="Noodles & Snacks", brand="Kurkure", unit="90g", price=20, stock=50, low_stock_threshold=15,
                 description="Kurkure Masala Munch 90g", aliases=["kurkure", "kurkure masala"]),
        _product(name="Lays Classic Salted", category="Noodles & Snacks", brand="Lays", unit="52g", price=20, stock=55, low_stock_threshold=15,
                 description="Lays Classic Salted Chips 52g", aliases=["lays", "chips", "lays chips", "aloo chips"]),
        _product(name="Haldiram Namkeen Bhujia", category="Noodles & Snacks", brand="Haldiram's", unit="200g", price=60, stock=25, low_stock_threshold=8,
                 description="Haldiram's Bhujia Namkeen 200g", aliases=["bhujia", "namkeen", "haldiram bhujia", "haldiram"]),
        _product(name="Maggi Family Pack", category="Noodles & Snacks", brand="Maggi", unit="560g", price=108, stock=32, low_stock_threshold=8,
                 description="Maggi 2-Minute Masala Family Pack 8×70g", aliases=["maggi pack", "maggi family"]),
        _product(name="Top Ramen Curry", category="Noodles & Snacks", brand="Nissin", unit="70g", price=14, stock=40, low_stock_threshold=10,
                 description="Nissin Top Ramen Curry Noodles 70g", aliases=["top ramen", "ramen"]),
        _product(name="Bingo Mad Angles", category="Noodles & Snacks", brand="Bingo", unit="80g", price=20, stock=38, low_stock_threshold=10,
                 description="Bingo Mad Angles Achaari Masti 80g", aliases=["bingo", "mad angles"]),
        _product(name="Uncle Chipps Spicy Treat", category="Noodles & Snacks", brand="Uncle Chipps", unit="55g", price=20, stock=42, low_stock_threshold=10,
                 description="Uncle Chipps Spicy Treat 55g", aliases=["uncle chips", "uncle chipps"]),
        _product(name="Haldiram Aloo Bhujia", category="Noodles & Snacks", brand="Haldiram's", unit="200g", price=55, stock=20, low_stock_threshold=6,
                 description="Haldiram's Aloo Bhujia 200g", aliases=["aloo bhujia"]),

        # ── Salt & Spices ──
        _product(name="Tata Salt", category="Salt & Spices", brand="Tata", unit="1kg", price=28, stock=50, low_stock_threshold=10,
                 description="Tata Salt Iodised Salt 1kg", aliases=["salt", "tata salt", "namak", "tata namak", "iodised salt"]),
        _product(name="Catch Turmeric Powder", category="Salt & Spices", brand="Catch", unit="200g", price=55, stock=35, low_stock_threshold=8,
                 description="Catch Turmeric Powder 200g", aliases=["haldi", "turmeric", "haldi powder"]),
        _product(name="MDH Chana Masala", category="Salt & Spices", brand="MDH", unit="100g", price=72, stock=40, low_stock_threshold=8,
                 description="MDH Chana Masala 100g", aliases=["chana masala", "mdh masala", "chole masala"]),
        _product(name="MDH Garam Masala", category="Salt & Spices", brand="MDH", unit="100g", price=85, stock=30, low_stock_threshold=5,
                 description="MDH Deggi Mirch Garam Masala 100g", aliases=["garam masala", "mdh garam masala"]),
        _product(name="Everest Red Chilli Powder", category="Salt & Spices", brand="Everest", unit="200g", price=68, stock=38, low_stock_threshold=8,
                 description="Everest Tikhalal Red Chilli Powder 200g", aliases=["laal mirch", "red chilli", "mirchi powder", "chilli powder"]),
        _product(name="Catch Jeera Powder", category="Salt & Spices", brand="Catch", unit="100g", price=45, stock=25, low_stock_threshold=5,
                 description="Catch Jeera (Cumin) Powder 100g", aliases=["jeera", "cumin", "jeera powder"]),
        _product(name="Tata Salt Lite", category="Salt & Spices", brand="Tata", unit="1kg", price=48, stock=18, low_stock_threshold=5,
                 description="Tata Salt Lite Low Sodium 1kg", aliases=["tata lite", "low sodium salt"]),
        _product(name="MDH Kitchen King", category="Salt & Spices", brand="MDH", unit="100g", price=78, stock=22, low_stock_threshold=5,
                 description="MDH Kitchen King Masala 100g", aliases=["kitchen king", "mdh kitchen king"]),
        _product(name="Everest Pav Bhaji Masala", category="Salt & Spices", brand="Everest", unit="100g", price=72, stock=16, low_stock_threshold=4,
                 description="Everest Pav Bhaji Masala 100g", aliases=["pav bhaji masala"]),
        _product(name="Catch Coriander Powder", category="Salt & Spices", brand="Catch", unit="200g", price=52, stock=24, low_stock_threshold=6,
                 description="Catch Dhania Powder 200g", aliases=["dhania", "coriander powder"]),

        # ── Dairy ──
        _product(name="Amul Taaza Milk", category="Dairy", brand="Amul", unit="1L", price=30, stock=60, low_stock_threshold=15,
                 description="Amul Taaza Homogenised Toned Milk 1L", aliases=["milk", "doodh", "amul milk", "amul doodh", "taaza"]),
        _product(name="Amul Butter", category="Dairy", brand="Amul", unit="100g", price=56, stock=40, low_stock_threshold=10,
                 description="Amul Pasteurised Butter 100g", aliases=["butter", "amul butter", "makhan"]),
        _product(name="Mother Dairy Curd", category="Dairy", brand="Mother Dairy", unit="400g", price=35, stock=30, low_stock_threshold=8,
                 description="Mother Dairy Classic Curd 400g", aliases=["curd", "dahi", "mother dairy dahi"]),
        _product(name="Amul Cheese Slices", category="Dairy", brand="Amul", unit="200g", price=110, stock=15, low_stock_threshold=5,
                 description="Amul Cheese Slices 200g (10 slices)", aliases=["cheese", "cheese slice", "amul cheese"]),
        _product(name="Amul Paneer", category="Dairy", brand="Amul", unit="200g", price=90, stock=20, low_stock_threshold=5,
                 description="Amul Fresh Paneer 200g", aliases=["paneer", "amul paneer", "cottage cheese"]),
        _product(name="Amul Gold Milk", category="Dairy", brand="Amul", unit="1L", price=68, stock=35, low_stock_threshold=10,
                 description="Amul Gold Full Cream Milk 1L", aliases=["full cream milk", "amul gold", "gold milk"]),
        _product(name="Mother Dairy Milk", category="Dairy", brand="Mother Dairy", unit="1L", price=32, stock=40, low_stock_threshold=12,
                 description="Mother Dairy Toned Milk 1L", aliases=["mother dairy milk", "md doodh"]),
        _product(name="Amul Dahi Cup", category="Dairy", brand="Amul", unit="400g", price=38, stock=22, low_stock_threshold=8,
                 description="Amul Masti Dahi 400g", aliases=["amul dahi", "amul curd"]),
        _product(name="Amul Fresh Cream", category="Dairy", brand="Amul", unit="250ml", price=68, stock=14, low_stock_threshold=4,
                 description="Amul Fresh Cream 250ml", aliases=["cream", "fresh cream", "malai"]),
        _product(name="Britannia Cheese Cubes", category="Dairy", brand="Britannia", unit="200g", price=125, stock=12, low_stock_threshold=4,
                 description="Britannia Cheese Cubes 200g", aliases=["cheese cubes"]),

        # ── Biscuits & Cookies ──
        _product(name="Parle-G Biscuits", category="Biscuits & Cookies", brand="Parle", unit="250g", price=30, stock=80, low_stock_threshold=20,
                 description="Parle-G Original Glucose Biscuits 250g",
                 aliases=["parle g", "parle", "glucose biscuit", "parle biscuit", "parle-g"]),
        _product(name="Britannia Good Day", category="Biscuits & Cookies", brand="Britannia", unit="200g", price=40, stock=50, low_stock_threshold=12,
                 description="Britannia Good Day Butter Cookies 200g", aliases=["good day", "britannia biscuit", "good day biscuit"]),
        _product(name="Oreo Biscuits", category="Biscuits & Cookies", brand="Cadbury", unit="120g", price=30, stock=45, low_stock_threshold=12,
                 description="Cadbury Oreo Vanilla Creme Biscuits 120g", aliases=["oreo", "oreo biscuit", "cadbury oreo"]),
        _product(name="Britannia Marie Gold", category="Biscuits & Cookies", brand="Britannia", unit="250g", price=35, stock=40, low_stock_threshold=10,
                 description="Britannia Marie Gold Tea Time Biscuits 250g", aliases=["marie", "marie gold", "marie biscuit"]),
        _product(name="Hide & Seek", category="Biscuits & Cookies", brand="Parle", unit="200g", price=45, stock=35, low_stock_threshold=8,
                 description="Parle Hide & Seek Chocolate Chip Cookies 200g", aliases=["hide and seek", "hide seek", "chocolate biscuit"]),
        _product(name="Sunfeast Dark Fantasy", category="Biscuits & Cookies", brand="Sunfeast", unit="75g", price=35, stock=28, low_stock_threshold=8,
                 description="Sunfeast Dark Fantasy Choco Fills 75g", aliases=["dark fantasy"]),
        _product(name="Monaco Salted Biscuits", category="Biscuits & Cookies", brand="Parle", unit="200g", price=30, stock=30, low_stock_threshold=8,
                 description="Parle Monaco Classic Salted 200g", aliases=["monaco"]),
        _product(name="Britannia Bourbon", category="Biscuits & Cookies", brand="Britannia", unit="150g", price=40, stock=26, low_stock_threshold=8,
                 description="Britannia Bourbon Chocolate Cream 150g", aliases=["bourbon"]),

        # ── Beverages ──
        _product(name="Tata Tea Gold", category="Beverages", brand="Tata", unit="250g", price=145, stock=35, low_stock_threshold=8,
                 description="Tata Tea Gold Leaf Tea 250g", aliases=["tea", "chai", "tata tea", "tata chai", "chai patti"]),
        _product(name="Nescafe Classic Coffee", category="Beverages", brand="Nescafe", unit="100g", price=265, stock=18, low_stock_threshold=5,
                 description="Nescafe Classic Instant Coffee 100g", aliases=["coffee", "nescafe", "instant coffee"]),
        _product(name="Bournvita", category="Beverages", brand="Cadbury", unit="500g", price=235, stock=15, low_stock_threshold=5,
                 description="Cadbury Bournvita Health Drink 500g", aliases=["bournvita", "cadbury bournvita", "health drink"]),
        _product(name="Horlicks", category="Beverages", brand="HUL", unit="500g", price=275, stock=12, low_stock_threshold=4,
                 description="Horlicks Health & Nutrition Drink 500g", aliases=["horlicks", "health drink horlicks"]),
        _product(name="Frooti Mango Drink", category="Beverages", brand="Parle Agro", unit="200ml", price=10, stock=100, low_stock_threshold=25,
                 description="Frooti Mango Drink 200ml Tetra Pack", aliases=["frooti", "mango juice", "frooti juice"]),
        _product(name="Thums Up", category="Beverages", brand="Coca-Cola", unit="750ml", price=40, stock=50, low_stock_threshold=15,
                 description="Thums Up Charged Cola 750ml", aliases=["thums up", "cola", "cold drink", "thumps up"]),
        _product(name="Red Label Tea", category="Beverages", brand="Brooke Bond", unit="250g", price=125, stock=22, low_stock_threshold=6,
                 description="Brooke Bond Red Label Tea 250g", aliases=["red label", "brooke bond"]),
        _product(name="Taj Mahal Tea", category="Beverages", brand="Brooke Bond", unit="250g", price=185, stock=14, low_stock_threshold=4,
                 description="Taj Mahal Tea 250g", aliases=["taj mahal tea", "taj tea"]),
        _product(name="Coca-Cola", category="Beverages", brand="Coca-Cola", unit="750ml", price=40, stock=48, low_stock_threshold=12,
                 description="Coca-Cola 750ml", aliases=["coke", "coca cola"]),
        _product(name="Sprite", category="Beverages", brand="Coca-Cola", unit="750ml", price=40, stock=36, low_stock_threshold=10,
                 description="Sprite 750ml", aliases=["sprite"]),
        _product(name="Maaza Mango", category="Beverages", brand="Coca-Cola", unit="1.2L", price=55, stock=28, low_stock_threshold=8,
                 description="Maaza Mango Drink 1.2L", aliases=["maaza", "maza"]),
        _product(name="Bisleri Water 1L", category="Beverages", brand="Bisleri", unit="1L", price=20, stock=80, low_stock_threshold=20,
                 description="Bisleri Mineral Water 1L", aliases=["water", "bisleri", "bottle water", "paani"]),

        # ── Essentials ──
        _product(name="Sugar", category="Essentials", brand="Local", unit="1kg", price=48, stock=60, low_stock_threshold=15,
                 description="Refined White Sugar 1kg", aliases=["sugar", "cheeni", "shakkar"]),
        _product(name="Jaggery (Gur)", category="Essentials", brand="Local", unit="1kg", price=65, stock=20, low_stock_threshold=5,
                 description="Organic Jaggery 1kg", aliases=["gur", "jaggery", "gud"]),
        _product(name="Poha (Flattened Rice)", category="Essentials", brand="Local", unit="500g", price=35, stock=25, low_stock_threshold=8,
                 description="Medium Poha (Flattened Rice) 500g", aliases=["poha", "chiwda", "flattened rice"]),
        _product(name="Suji (Semolina)", category="Essentials", brand="Local", unit="500g", price=32, stock=25, low_stock_threshold=8,
                 description="Fine Suji (Semolina/Rava) 500g", aliases=["suji", "rava", "semolina", "sooji"]),
        _product(name="Tata Sampann Toor Dal", category="Essentials", brand="Tata", unit="1kg", price=175, stock=16, low_stock_threshold=5,
                 description="Tata Sampann Unpolished Toor Dal 1kg", aliases=["tata dal", "sampann toor"]),
        _product(name="Aashirvaad Salt", category="Essentials", brand="Aashirvaad", unit="1kg", price=26, stock=30, low_stock_threshold=8,
                 description="Aashirvaad Iodised Salt 1kg", aliases=["aashirvaad namak"]),
        _product(name="MTR Instant Poha Mix", category="Essentials", brand="MTR", unit="60g", price=25, stock=20, low_stock_threshold=6,
                 description="MTR Breakfast Poha Mix 60g", aliases=["mtr poha", "instant poha"]),

        # ── Personal Care ──
        _product(name="Dettol Soap", category="Personal Care", brand="Dettol", unit="75g", price=42, stock=40, low_stock_threshold=10,
                 description="Dettol Original Antibacterial Bar Soap 75g", aliases=["dettol", "dettol soap", "sabun"]),
        _product(name="Colgate Toothpaste", category="Personal Care", brand="Colgate", unit="200g", price=95, stock=30, low_stock_threshold=8,
                 description="Colgate Strong Teeth Toothpaste 200g", aliases=["colgate", "toothpaste", "dant manjan"]),
        _product(name="Head & Shoulders Shampoo", category="Personal Care", brand="P&G", unit="180ml", price=195, stock=15, low_stock_threshold=5,
                 description="Head & Shoulders Anti-Dandruff Shampoo 180ml", aliases=["shampoo", "head shoulders", "anti dandruff"]),
        _product(name="Lifebuoy Handwash", category="Personal Care", brand="HUL", unit="190ml", price=49, stock=25, low_stock_threshold=8,
                 description="Lifebuoy Total 10 Handwash 190ml", aliases=["handwash", "lifebuoy", "hand wash"]),
        _product(name="Vim Dishwash Bar", category="Personal Care", brand="HUL", unit="200g", price=18, stock=50, low_stock_threshold=10,
                 description="Vim Dishwash Bar 200g", aliases=["vim", "bartan sabun", "dish wash"]),
        _product(name="Dove Beauty Bar", category="Personal Care", brand="Dove", unit="75g", price=48, stock=22, low_stock_threshold=6,
                 description="Dove Cream Beauty Bathing Bar 75g", aliases=["dove", "dove soap"]),
        _product(name="Pepsodent Toothpaste", category="Personal Care", brand="Pepsodent", unit="150g", price=72, stock=18, low_stock_threshold=5,
                 description="Pepsodent Germicheck 150g", aliases=["pepsodent"]),
        _product(name="Clinic Plus Shampoo", category="Personal Care", brand="HUL", unit="175ml", price=85, stock=16, low_stock_threshold=5,
                 description="Clinic Plus Strong & Long Shampoo 175ml", aliases=["clinic plus"]),
        _product(name="Dettol Hand Sanitizer", category="Personal Care", brand="Dettol", unit="50ml", price=35, stock=28, low_stock_threshold=8,
                 description="Dettol Instant Hand Sanitizer 50ml", aliases=["sanitizer", "hand sanitizer"]),

        # ── Household ──
        _product(name="Surf Excel Detergent", category="Household", brand="Surf Excel", unit="1kg", price=195, stock=25, low_stock_threshold=6,
                 description="Surf Excel Easy Wash Detergent Powder 1kg", aliases=["surf excel", "detergent", "washing powder", "surf"]),
        _product(name="Harpic Toilet Cleaner", category="Household", brand="Harpic", unit="500ml", price=95, stock=15, low_stock_threshold=5,
                 description="Harpic Power Plus Toilet Cleaner 500ml", aliases=["harpic", "toilet cleaner"]),
        _product(name="Lizol Floor Cleaner", category="Household", brand="Lizol", unit="500ml", price=115, stock=18, low_stock_threshold=5,
                 description="Lizol Disinfectant Surface Cleaner 500ml", aliases=["lizol", "floor cleaner", "phenyl"]),
        _product(name="Hit Cockroach Spray", category="Household", brand="Godrej", unit="200ml", price=145, stock=10, low_stock_threshold=3,
                 description="Hit Cockroach & Crawling Insect Killer Spray 200ml", aliases=["hit spray", "cockroach spray", "khatmal spray"]),
        _product(name="Tide Plus Detergent", category="Household", brand="Tide", unit="1kg", price=185, stock=18, low_stock_threshold=5,
                 description="Tide Plus Extra Power 1kg", aliases=["tide", "tide detergent"]),
        _product(name="Rin Detergent Bar", category="Household", brand="Rin", unit="250g", price=22, stock=40, low_stock_threshold=10,
                 description="Rin Advanced Detergent Bar 250g", aliases=["rin", "rin bar"]),
        _product(name="Good Knight Liquid", category="Household", brand="Good Knight", unit="45ml", price=78, stock=20, low_stock_threshold=6,
                 description="Good Knight Gold Flash Liquid Refill", aliases=["goodknight", "mosquito", "liquid vaporiser"]),
        _product(name="Colin Glass Cleaner", category="Household", brand="Colin", unit="500ml", price=99, stock=14, low_stock_threshold=4,
                 description="Colin Glass & Household Cleaner 500ml", aliases=["colin", "glass cleaner"]),

        # ── Bread & Breakfast ──
        _product(name="Britannia Bread", category="Bread & Breakfast", brand="Britannia", unit="400g", price=45, stock=24, low_stock_threshold=8,
                 description="Britannia Healthy Slice Bread 400g", aliases=["bread", "double roti", "pav bread"]),
        _product(name="English Oven Brown Bread", category="Bread & Breakfast", brand="English Oven", unit="400g", price=50, stock=16, low_stock_threshold=5,
                 description="English Oven Whole Wheat Bread 400g", aliases=["brown bread"]),
        _product(name="Kissan Mixed Fruit Jam", category="Bread & Breakfast", brand="Kissan", unit="500g", price=145, stock=18, low_stock_threshold=5,
                 description="Kissan Mixed Fruit Jam 500g", aliases=["jam", "kissan jam"]),
        _product(name="Nutella", category="Bread & Breakfast", brand="Ferrero", unit="350g", price=399, stock=8, low_stock_threshold=3,
                 description="Nutella Hazelnut Spread 350g", aliases=["nutella"]),
        _product(name="Kellogg's Corn Flakes", category="Bread & Breakfast", brand="Kellogg's", unit="475g", price=185, stock=12, low_stock_threshold=4,
                 description="Kellogg's Corn Flakes Original 475g", aliases=["cornflakes", "corn flakes"]),
        _product(name="Quaker Oats", category="Bread & Breakfast", brand="Quaker", unit="400g", price=89, stock=15, low_stock_threshold=4,
                 description="Quaker Oats 400g", aliases=["oats", "quaker"]),

        # ── Baby & Kids ──
        _product(name="Cerelac Wheat", category="Baby & Kids", brand="Nestle", unit="300g", price=249, stock=10, low_stock_threshold=3,
                 description="Nestle Cerelac Wheat Apple 300g", aliases=["cerelac", "baby food"]),
        _product(name="Amul Kool Kesar", category="Baby & Kids", brand="Amul", unit="180ml", price=25, stock=36, low_stock_threshold=10,
                 description="Amul Kool Kesar Milkshake 180ml", aliases=["amul kool", "milkshake"]),
        _product(name="Pediasure", category="Baby & Kids", brand="Abbott", unit="400g", price=620, stock=6, low_stock_threshold=2,
                 description="Pediasure Vanilla 400g", aliases=["pediasure"]),
    ]


def all_customers():
    return [
        Customer(name="Rahul Sharma", phone="9876543210", address="42, Sector 15, Noida, UP 201301",
                 email="rahul.sharma@gmail.com", preferred_time="Evening"),
        Customer(name="Priya Verma", phone="9876543211", address="B-12, Lajpat Nagar-II, New Delhi 110024",
                 email="priya.verma@outlook.com", preferred_time="Morning"),
        Customer(name="Amit Kumar", phone="9876543212", address="Flat 3A, C-Block, Green Park Extension, New Delhi 110016",
                 email="amit.kumar22@gmail.com", preferred_time="Afternoon"),
        Customer(name="Sunita Devi", phone="9876543213", address="House 7, WEA Karol Bagh, New Delhi 110005",
                 email="", preferred_time="Morning"),
        Customer(name="Vikram Singh", phone="9876543214", address="A-1/302, Dwarka Sector 10, New Delhi 110075",
                 email="vikram.s@yahoo.com", preferred_time="Evening"),
        Customer(name="Neha Gupta", phone="9876543215", address="D-56, Vasant Kunj, New Delhi 110070",
                 email="neha.gupta@gmail.com", preferred_time="Morning"),
        Customer(name="Rajesh Patel", phone="9876543216", address="12/4, Mayur Vihar Phase-1, New Delhi 110091",
                 email="rajesh.patel@hotmail.com", preferred_time="Afternoon"),
        Customer(name="Anjali Mishra", phone="9876543217", address="F-78, Rohini Sector 7, New Delhi 110085",
                 email="anjali.m@gmail.com", preferred_time="Evening"),
        Customer(name="Deepak Joshi", phone="9876543218", address="Plot 23, Indirapuram, Ghaziabad, UP 201014",
                 email="deepak.joshi@gmail.com", preferred_time="Morning"),
        Customer(name="Meena Agarwal", phone="9876543219", address="B-34, Pitampura, New Delhi 110034",
                 email="meena.ag@gmail.com", preferred_time="Afternoon"),
        Customer(name="Suresh Yadav", phone="9876543220", address="65, Tilak Nagar, New Delhi 110018",
                 email="", preferred_time="Evening"),
        Customer(name="Pooja Sharma", phone="9876543221", address="H-91, Saket, New Delhi 110017",
                 email="pooja.sharma@gmail.com", preferred_time="Morning"),
        Customer(name="Manoj Tiwari", phone="9876543222", address="22/B, Janakpuri C-Block, New Delhi 110058",
                 email="manoj.t@outlook.com", preferred_time="Afternoon"),
        Customer(name="Kavita Reddy", phone="9876543223", address="Flat 5B, Greater Kailash-I, New Delhi 110048",
                 email="kavita.r@gmail.com", preferred_time="Evening"),
        Customer(name="Arun Mehta", phone="9876543224", address="15, Defence Colony, New Delhi 110024",
                 email="arun.mehta@gmail.com", preferred_time="Morning"),
        Customer(name="Rekha Bansal", phone="9876543225", address="C-12, Paschim Vihar, New Delhi 110063",
                 email="rekha.b@yahoo.com", preferred_time="Afternoon"),
        Customer(name="Sanjay Kapoor", phone="9876543226", address="48, Model Town-II, New Delhi 110009",
                 email="sanjay.k@gmail.com", preferred_time="Evening"),
        Customer(name="Nisha Pandey", phone="9876543227", address="G-67, Ashok Vihar Phase-I, New Delhi 110052",
                 email="nisha.p@gmail.com", preferred_time="Morning"),
        Customer(name="Ravi Shankar", phone="9876543228", address="3/14, Malviya Nagar, New Delhi 110017",
                 email="ravi.shankar@gmail.com", preferred_time="Afternoon"),
        Customer(name="Anita Singh", phone="9876543229", address="K-29, Hauz Khas, New Delhi 110016",
                 email="anita.singh@outlook.com", preferred_time="Evening"),
        Customer(name="Farhan Qureshi", phone="9876543230", address="14, Zakir Nagar, Okhla, New Delhi 110025",
                 email="farhan.q@gmail.com", preferred_time="Evening"),
        Customer(name="Lakshmi Iyer", phone="9876543231", address="9, CR Park, New Delhi 110019",
                 email="lakshmi.iyer@gmail.com", preferred_time="Morning"),
        Customer(name="Harpreet Kaur", phone="9876543232", address="88, Punjabi Bagh West, New Delhi 110026",
                 email="harpreet.k@gmail.com", preferred_time="Afternoon"),
        Customer(name="Mohammed Irfan", phone="9876543233", address="21, Jamia Nagar, New Delhi 110025",
                 email="", preferred_time="Evening"),
        Customer(name="Sneha Nair", phone="9876543234", address="C-4, Chittaranjan Park, New Delhi 110019",
                 email="sneha.nair@gmail.com", preferred_time="Morning"),
        Customer(name="Gaurav Malhotra", phone="9876543235", address="502, Wave City Center, Noida 201301",
                 email="gaurav.m@gmail.com", preferred_time="Evening"),
        Customer(name="Divya Chauhan", phone="9876543236", address="11, Rajendra Nagar, New Delhi 110060",
                 email="divya.c@gmail.com", preferred_time="Afternoon"),
        Customer(name="Imran Khan", phone="9876543237", address="A-19, Nizamuddin East, New Delhi 110013",
                 email="imran.k@gmail.com", preferred_time="Evening"),
        Customer(name="Shweta Rao", phone="9876543238", address="B-8, South Extension Part-1, New Delhi 110049",
                 email="shweta.rao@gmail.com", preferred_time="Morning"),
        Customer(name="Yogesh Rawat", phone="9876543239", address="76, Govindpuri, New Delhi 110019",
                 email="", preferred_time="Afternoon"),
        Customer(name="Kiran Desai", phone="9876543240", address="3, Patel Nagar West, New Delhi 110008",
                 email="kiran.desai@gmail.com", preferred_time="Morning"),
        Customer(name="Abhishek Jain", phone="9876543241", address="P-22, Greater Noida West, UP 201306",
                 email="abhishek.j@gmail.com", preferred_time="Evening"),
        Customer(name="Ritu Saxena", phone="9876543242", address="44, Shalimar Bagh, New Delhi 110088",
                 email="ritu.saxena@gmail.com", preferred_time="Afternoon"),
        Customer(name="Naveen Reddy", phone="9876543243", address="G-11, Kailash Colony, New Delhi 110048",
                 email="naveen.r@gmail.com", preferred_time="Evening"),
        Customer(name="Pallavi Joshi", phone="9876543244", address="18, Civil Lines, New Delhi 110054",
                 email="pallavi.j@gmail.com", preferred_time="Morning"),
        Customer(name="Tarun Bhatia", phone="9876543245", address="9/2, Rajouri Garden, New Delhi 110027",
                 email="tarun.b@gmail.com", preferred_time="Afternoon"),
        Customer(name="Ayesha Siddiqui", phone="9876543246", address="55, Abul Fazal Enclave, New Delhi 110025",
                 email="ayesha.s@gmail.com", preferred_time="Evening"),
        Customer(name="Rohit Chauhan", phone="9876543247", address="31, Vaishali, Ghaziabad, UP 201010",
                 email="rohit.c@gmail.com", preferred_time="Morning"),
        Customer(name="Geeta Nanda", phone="9876543248", address="C-90, Janakpuri B-Block, New Delhi 110058",
                 email="geeta.nanda@gmail.com", preferred_time="Afternoon"),
        Customer(name="Sameer Ali", phone="9876543249", address="12, Batla House, New Delhi 110025",
                 email="", preferred_time="Evening"),
    ]


def all_delivery_persons():
    return [
        DeliveryPerson(name="Raju", phone="9988776601", vehicle_type="Bicycle", area="Sector 15, Noida", is_available=True),
        DeliveryPerson(name="Mohan", phone="9988776602", vehicle_type="Scooter", area="Lajpat Nagar, South Delhi", is_available=True),
        DeliveryPerson(name="Bahadur", phone="9988776603", vehicle_type="Bicycle", area="Green Park, Karol Bagh", is_available=True),
        DeliveryPerson(name="Pappu", phone="9988776604", vehicle_type="Scooter", area="Dwarka, Janakpuri", is_available=True),
        DeliveryPerson(name="Sonu", phone="9988776605", vehicle_type="E-Bike", area="Rohini, Pitampura, Model Town", is_available=True),
        DeliveryPerson(name="Imran", phone="9988776606", vehicle_type="Scooter", area="Okhla, Jamia, Nizamuddin", is_available=True),
        DeliveryPerson(name="Deepak", phone="9988776607", vehicle_type="E-Bike", area="Saket, Malviya Nagar, Hauz Khas", is_available=True),
        DeliveryPerson(name="Karan", phone="9988776608", vehicle_type="Scooter", area="Mayur Vihar, Indirapuram, Vaishali", is_available=True),
    ]


def seed_products(db: Session):
    existing = {p.name for p in db.query(Product.name).all()}
    to_add = [p for p in all_catalog_products() if p.name not in existing]
    if to_add:
        db.add_all(to_add)
        db.commit()

    # Backfill CP on older rows (SP stays as price)
    dirty = False
    for product in db.query(Product).all():
        if not product.cost_price:
            product.cost_price = round(
                product.price * (1 - _margin_for(product.category)), 2
            )
            dirty = True
    if dirty:
        db.commit()


def seed_customers(db: Session):
    existing = {c.phone for c in db.query(Customer.phone).all()}
    to_add = [c for c in all_customers() if c.phone not in existing]
    if to_add:
        db.add_all(to_add)
        db.commit()


def seed_delivery_persons(db: Session):
    existing = {p.phone for p in db.query(DeliveryPerson.phone).all()}
    to_add = [p for p in all_delivery_persons() if p.phone not in existing]
    if to_add:
        db.add_all(to_add)
        db.commit()


def _product_map(db: Session):
    return {p.name: p for p in db.query(Product).all()}


def _add_history_order(db, customer, days_ago, items, products, delivery=True):
    """Create a past delivered order without changing current live stock."""
    now = datetime.now(timezone.utc) - timedelta(days=days_ago)
    resolved = []
    subtotal = 0.0
    for name, qty in items:
        product = products.get(name)
        if not product:
            continue
        total = round(product.price * qty, 2)
        subtotal += total
        resolved.append((product, qty, product.price, total, product.cost_price or 0))
    if not resolved:
        return
    fee = 30.0 if delivery else 0.0
    order = Order(
        customer_id=customer.id,
        status="delivered",
        subtotal=round(subtotal, 2),
        delivery_fee=fee,
        total=round(subtotal + fee, 2),
        delivery_address=customer.address,
        delivery_requested=delivery,
        original_request="history_seed",
        channel="history_seed",
        created_at=now,
    )
    db.add(order)
    db.flush()
    for product, qty, unit_price, total, cost_price in resolved:
        db.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
            cost_price=cost_price,
            total_price=total,
        ))


def seed_historical_orders(db: Session):
    """Give regulars a buying history so phone lookup shows prior orders."""
    existing = db.query(Order).filter(Order.channel == "history_seed").count()
    if existing > 0:
        return

    products = _product_map(db)
    by_phone = {c.phone: c for c in db.query(Customer).all()}

    plans = [
        ("9876543210", [
            (18, [("Aashirvaad Atta", 2), ("Fortune Sunflower Oil", 1), ("Maggi 2-Minute Noodles", 6)]),
            (11, [("Amul Taaza Milk", 2), ("Parle-G Biscuits", 3), ("Tata Salt", 1)]),
            (4, [("Toor Dal", 1), ("Tata Tea Gold", 1), ("Sugar", 2)]),
        ]),
        ("9876543211", [
            (15, [("Amul Butter", 1), ("Britannia Bread", 2), ("Kissan Mixed Fruit Jam", 1)]),
            (6, [("Mother Dairy Curd", 2), ("Amul Paneer", 1)]),
        ]),
        ("9876543212", [
            (20, [("India Gate Basmati Rice", 1), ("Fortune Mustard Oil", 1)]),
            (9, [("Maggi 2-Minute Noodles", 8), ("Lays Classic Salted", 4)]),
            (2, [("Thums Up", 2), ("Oreo Biscuits", 2)]),
        ]),
        ("9876543213", [
            (12, [("Aashirvaad Atta", 1), ("Toor Dal", 1), ("Tata Salt", 1), ("Sugar", 1)]),
            (3, [("Amul Taaza Milk", 3), ("Parle-G Biscuits", 2)]),
        ]),
        ("9876543214", [
            (8, [("Surf Excel Detergent", 1), ("Vim Dishwash Bar", 2), ("Dettol Soap", 3)]),
        ]),
        ("9876543215", [
            (14, [("Saffola Gold Oil", 1), ("Quaker Oats", 1), ("Amul Gold Milk", 2)]),
            (5, [("Nescafe Classic Coffee", 1), ("Britannia Marie Gold", 1)]),
        ]),
        ("9876543216", [
            (10, [("Rajma", 1), ("MDH Chana Masala", 1), ("India Gate Basmati Rice", 1)]),
        ]),
        ("9876543217", [
            (7, [("Colgate Toothpaste", 1), ("Clinic Plus Shampoo", 1), ("Dove Beauty Bar", 2)]),
        ]),
        ("9876543221", [
            (16, [("Bournvita", 1), ("Amul Taaza Milk", 2), ("Parle-G Biscuits", 2)]),
            (1, [("Frooti Mango Drink", 6), ("Kurkure Masala Munch", 3)]),
        ]),
        ("9876543230", [
            (13, [("Fortune Sunflower Oil", 1), ("Moong Dal", 1), ("Catch Turmeric Powder", 1)]),
        ]),
        ("9876543235", [
            (9, [("Maggi Family Pack", 1), ("Amul Cheese Slices", 1), ("Coca-Cola", 2)]),
            (2, [("Lays Classic Salted", 3), ("Hide & Seek", 1)]),
        ]),
        ("9876543247", [
            (21, [("Aashirvaad Atta", 1), ("Fortune Sunflower Oil", 1), ("Tata Salt", 1), ("Sugar", 2), ("Toor Dal", 1)]),
            (8, [("Amul Taaza Milk", 4), ("Mother Dairy Curd", 2)]),
        ]),
    ]

    for phone, orders in plans:
        customer = by_phone.get(phone)
        if not customer:
            continue
        for days_ago, items in orders:
            _add_history_order(db, customer, days_ago, items, products)

    db.commit()


def seed_database(db: Session):
    """Run all seed operations (additive)."""
    seed_products(db)
    seed_customers(db)
    seed_delivery_persons(db)
    seed_historical_orders(db)
    _backfill_order_item_cost(db)


def _backfill_order_item_cost(db: Session):
    items = db.query(OrderItem).filter(
        (OrderItem.cost_price == None) | (OrderItem.cost_price == 0)
    ).all()
    if not items:
        return
    products = {p.id: p for p in db.query(Product).all()}
    for item in items:
        product = products.get(item.product_id)
        if product:
            item.cost_price = product.cost_price or round(item.unit_price * 0.85, 2)
    db.commit()
