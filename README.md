# Telegram Order Bot

A Telegram bot that accepts orders with a product catalog and cart, backed by
PostgreSQL, plus a web admin panel (Flask) to manage products and orders.

## Structure

```
tg-order-bot/
├── bot.py             # Telegram bot (aiogram 3): catalog, cart, checkout, order history
├── admin.py           # Flask admin panel: login, product CRUD, order status management
├── database.py        # SQLAlchemy models (Product, Order, OrderItem) + engine/session
├── config.py          # Configuration from .env
├── seed.py            # Optional: insert sample products
├── templates/         # Admin panel HTML templates
├── docker-compose.yml # PostgreSQL 16 (docker compose up -d db)
├── requirements.txt
└── .env.example
```

## Setup

1. Create a bot token with [@BotFather](https://t.me/BotFather).
2. Copy `.env.example` to `.env` and fill in `BOT_TOKEN`, DB credentials, and admin login.
3. Start PostgreSQL (or point `DATABASE_URL` at your own server):

   ```bash
   docker compose up -d db
   ```

4. Install dependencies and seed sample products:

   ```bash
   pip install -r requirements.txt
   python seed.py
   ```

## Run

Two processes (two terminals):

```bash
python bot.py      # Telegram bot (long polling)
python admin.py    # Admin panel at http://localhost:5000
```

## Usage

- **Bot**: `/start` → browse catalog → add items to cart → checkout with
  name, phone, address, comment → order is stored in PostgreSQL.
  "Мои заказы" shows the customer's order history and statuses.
- **Admin panel**: log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `.env`.
  Manage products (add/edit/delete/activate) and view orders, change their status
  (new → confirmed → preparing → delivering → completed / cancelled).

## Notes

- The cart is kept in memory per user; switching to a DB-backed cart is easy
  via a dedicated table if you need persistence across restarts.
- For production, serve the admin panel with gunicorn/waitress and use webhooks
  for the bot instead of long polling.
