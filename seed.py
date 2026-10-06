"""Seed the database with a few sample products."""
from database import Product, SessionLocal, init_db

SAMPLES = [
    ("Пицца Маргарита", "Томатный соус, моцарелла, базилик", 250.00),
    ("Пицца Пепперони", "Острая колбаса, сыр, соус", 320.00),
    ("Бургер классический", "Говяжья котлета, салат, соус", 280.00),
    ("Картофель фри", "Хрустящий картофель с кетчупом", 120.00),
]

if __name__ == "__main__":
    init_db()
    with SessionLocal() as s:
        if s.query(Product).count() == 0:
            for name, desc, price in SAMPLES:
                s.add(Product(name=name, description=desc, price=price))
            s.commit()
            print(f"Added {len(SAMPLES)} products")
        else:
            print("Products already exist, skipping")
