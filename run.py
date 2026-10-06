import asyncio
import os
import threading

from bot import main as bot_main
from admin import app


def run_bot():
    asyncio.run(bot_main())


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
