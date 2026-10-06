import asyncio
from collections import defaultdict

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN
from database import Order, OrderItem, Product, SessionLocal, init_db

dp = Dispatcher(storage=MemoryStorage())

# ---------------- i18n ----------------
LANGS = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
user_lang: dict[int, str] = {}
carts: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))

TEXT: dict[str, dict[str, str]] = {
    "welcome": {
        "uz": "Xush kelibsiz! Bu buyurtma qabul qilish boti.\nQuyidan amal tanlang.",
        "ru": "Добро пожаловать! Это бот приёма заказов.\nВыберите действие ниже.",
        "en": "Welcome! This is an order bot.\nChoose an action below.",
    },
    "catalog": {"uz": "🛍 Katalog", "ru": "🛍 Каталог", "en": "🛍 Catalog"},
    "cart": {"uz": "🛒 Savat", "ru": "🛒 Корзина", "en": "🛒 Cart"},
    "my_orders": {"uz": "📦 Buyurtmalarim", "ru": "📦 Мои заказы", "en": "📦 My orders"},
    "help_btn": {"uz": "ℹ️ Yordam", "ru": "ℹ️ Помощь", "en": "ℹ️ Help"},
    "lang_btn": {"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language"},
    "help": {
        "uz": "🛍 Katalog — mahsulotlar ro'yxati\n🛒 Savat — tanlangan mahsulotlar\n📦 Buyurtmalarim — buyurtmalar tarixi\n🌐 Til — tilni almashtirish\n\nBuyurtmani tasdiqlash uchun savatga o'tib «Rasmiylashtirish» tugmasini bosing.",
        "ru": "🛍 Каталог — список товаров\n🛒 Корзина — выбранные товары\n📦 Мои заказы — история заказов\n🌐 Язык — сменить язык\n\nЧтобы подтвердить заказ, откройте корзину и нажмите «Оформить».",
        "en": "🛍 Catalog — product list\n🛒 Cart — selected items\n📦 My orders — order history\n🌐 Language — change language\n\nTo confirm an order, open the cart and press checkout.",
    },
    "empty_catalog": {"uz": "Katalog hozir bo'sh.", "ru": "Каталог пока пуст.", "en": "Catalog is empty for now."},
    "price": {"uz": "Narxi", "ru": "Цена", "en": "Price"},
    "add_btn": {"uz": "➕ Savatga", "ru": "➕ В корзину", "en": "➕ Add to cart"},
    "added": {"uz": "Savatga qo'shildi ✅", "ru": "Добавлено в корзину ✅", "en": "Added to cart ✅"},
    "empty_cart": {"uz": "Savat bo'sh.", "ru": "Корзина пуста.", "en": "Cart is empty."},
    "your_order": {"uz": "*Buyurtmangiz:*", "ru": "*Ваш заказ:*", "en": "*Your order:*"},
    "total": {"uz": "*Jami", "ru": "*Итого", "en": "*Total"},
    "checkout_btn": {"uz": "✅ Rasmiylashtirish", "ru": "✅ Оформить заказ", "en": "✅ Checkout"},
    "clear_btn": {"uz": "🗑 Tozalash", "ru": "🗑 Очистить", "en": "🗑 Clear"},
    "cart_cleared": {"uz": "Savat tozalandi.", "ru": "Корзина очищена.", "en": "Cart cleared."},
    "ask_name": {"uz": "Ismingizni kiriting:", "ru": "Введите ваше имя:", "en": "Enter your name:"},
    "ask_phone": {"uz": "Telefon raqamingizni kiriting:", "ru": "Введите номер телефона:", "en": "Enter your phone number:"},
    "ask_address": {"uz": "Yetkazib berish manzilini kiriting:", "ru": "Введите адрес доставки:", "en": "Enter delivery address:"},
    "ask_comment": {"uz": "Buyurtmaga izoh (yo'q bo'lsa «-»):", "ru": "Комментарий к заказу (или «-» если нет):", "en": "Comment for the order (or «-» if none):"},
    "check_order": {"uz": "Buyurtmani tekshiring:", "ru": "Проверьте заказ:", "en": "Check your order:"},
    "name_label": {"uz": "Ism", "ru": "Имя", "en": "Name"},
    "phone_label": {"uz": "Telefon", "ru": "Телефон", "en": "Phone"},
    "address_label": {"uz": "Manzil", "ru": "Адрес", "en": "Address"},
    "comment_label": {"uz": "Izoh", "ru": "Комментарий", "en": "Comment"},
    "confirm_btn": {"uz": "✅ Tasdiqlash", "ru": "✅ Подтвердить", "en": "✅ Confirm"},
    "cancel_btn": {"uz": "❌ Bekor qilish", "ru": "❌ Отмена", "en": "❌ Cancel"},
    "order_done": {"uz": "✅ Buyurtma #{id} qabul qilindi! Tasdiqlashni kuting.", "ru": "✅ Заказ №{id} оформлен! Ожидайте подтверждения.", "en": "✅ Order #{id} placed! Please wait for confirmation."},
    "order_cancelled": {"uz": "Buyurtma bekor qilindi. Savat saqlandi.", "ru": "Заказ отменён. Корзина сохранена.", "en": "Order cancelled. Cart saved."},
    "no_orders": {"uz": "Sizda hali buyurtma yo'q.", "ru": "У вас пока нет заказов.", "en": "You have no orders yet."},
    "your_orders": {"uz": "*Buyurtmalaringiz:*", "ru": "*Ваши заказы:*", "en": "*Your orders:*"},
    "choose_lang": {"uz": "Tilni tanlang:", "ru": "Выберите язык:", "en": "Choose a language:"},
    "lang_set": {"uz": "Til o'zgartirildi: O'zbekcha ✅", "ru": "Язык изменён: Русский ✅", "en": "Language changed: English ✅"},
}


def t(key: str, user_id: int) -> str:
    lang = user_lang.get(user_id, "uz")
    return TEXT[key][lang]


def labels(key: str) -> set[str]:
    return {TEXT[key][lang] for lang in LANGS}


def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("catalog", user_id)), KeyboardButton(text=t("cart", user_id))],
            [KeyboardButton(text=t("my_orders", user_id)), KeyboardButton(text=t("help_btn", user_id))],
            [KeyboardButton(text=t("lang_btn", user_id))],
        ],
        resize_keyboard=True,
    )


class Checkout(StatesGroup):
    full_name = State()
    phone = State()
    address = State()
    comment = State()
    confirm = State()


def cart_total(user_id: int) -> tuple[float, list[str]]:
    total = 0.0
    lines = []
    with SessionLocal() as s:
        for pid, qty in carts[user_id].items():
            p = s.get(Product, pid)
            if not p:
                continue
            total += float(p.price) * qty
            lines.append(f"{p.name} × {qty} = {float(p.price) * qty:.2f}")
    return total, lines


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(t("welcome", message.from_user.id), reply_markup=main_menu(message.from_user.id))


@dp.message(F.text.in_(labels("help_btn")))
@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(t("help", message.from_user.id))


@dp.message(F.text.in_(labels("lang_btn")))
async def lang_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
        for code, name in LANGS.items()
    ])
    await message.answer(t("choose_lang", message.from_user.id), reply_markup=kb)


@dp.callback_query(F.data.startswith("lang:"))
async def lang_set(cb: CallbackQuery):
    code = cb.data.split(":")[1]
    user_lang[cb.from_user.id] = code
    await cb.message.answer(t("lang_set", cb.from_user.id), reply_markup=main_menu(cb.from_user.id))
    await cb.answer()


@dp.message(F.text.in_(labels("catalog")))
async def catalog(message: Message):
    uid = message.from_user.id
    with SessionLocal() as s:
        products = s.query(Product).filter_by(is_active=True).order_by(Product.id).all()
        data = [(p.id, p.name, float(p.price), p.description) for p in products]
    if not data:
        await message.answer(t("empty_catalog", uid))
        return
    for pid, name, price, desc in data:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"{t('add_btn', uid)} ({price:.2f})", callback_data=f"add:{pid}")
        ]])
        await message.answer(f"*{name}*\n{desc}\n{t('price', uid)}: {price:.2f}",
                             parse_mode="Markdown", reply_markup=kb)


@dp.callback_query(F.data.startswith("add:"))
async def add_to_cart(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    carts[cb.from_user.id][pid] += 1
    await cb.answer(t("added", cb.from_user.id))


@dp.message(F.text.in_(labels("cart")))
async def view_cart(message: Message):
    uid = message.from_user.id
    total, lines = cart_total(uid)
    if not lines:
        await message.answer(t("empty_cart", uid))
        return
    kb = InlineKeyboardBuilder()
    kb.button(text=t("checkout_btn", uid), callback_data="checkout")
    kb.button(text=t("clear_btn", uid), callback_data="clear_cart")
    kb.adjust(1)
    await message.answer(
        t("your_order", uid) + "\n" + "\n".join(lines) + f"\n\n{t('total', uid)}: {total:.2f}*",
        parse_mode="Markdown", reply_markup=kb.as_markup(),
    )


@dp.callback_query(F.data == "clear_cart")
async def clear_cart(cb: CallbackQuery):
    carts[cb.from_user.id].clear()
    await cb.message.edit_text(t("cart_cleared", cb.from_user.id))


@dp.callback_query(F.data == "checkout")
async def checkout_start(cb: CallbackQuery, state: FSMContext):
    total, lines = cart_total(cb.from_user.id)
    if not lines:
        await cb.answer(t("empty_cart", cb.from_user.id), show_alert=True)
        return
    await state.set_state(Checkout.full_name)
    await cb.message.answer(t("ask_name", cb.from_user.id))
    await cb.answer()


@dp.message(Checkout.full_name)
async def checkout_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(Checkout.phone)
    await message.answer(t("ask_phone", message.from_user.id))


@dp.message(Checkout.phone)
async def checkout_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Checkout.address)
    await message.answer(t("ask_address", message.from_user.id))


@dp.message(Checkout.address)
async def checkout_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(Checkout.comment)
    await message.answer(t("ask_comment", message.from_user.id))


@dp.message(Checkout.comment)
async def checkout_comment(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.update_data(comment="" if message.text == "-" else message.text)
    data = await state.get_data()
    total, lines = cart_total(uid)
    await state.update_data(total=total)
    await state.set_state(Checkout.confirm)
    kb = InlineKeyboardBuilder()
    kb.button(text=t("confirm_btn", uid), callback_data="confirm_order")
    kb.button(text=t("cancel_btn", uid), callback_data="cancel_order")
    kb.adjust(2)
    await message.answer(
        f"{t('check_order', uid)}\n\n" + "\n".join(lines)
        + f"\n\n{t('total', uid)[1:]}: {total:.2f}\n{t('name_label', uid)}: {data['full_name']}\n"
          f"{t('phone_label', uid)}: {data['phone']}\n{t('address_label', uid)}: {data['address']}\n"
          f"{t('comment_label', uid)}: {data.get('comment') or '-'}",
        reply_markup=kb.as_markup(),
    )


@dp.callback_query(Checkout.confirm, F.data == "confirm_order")
async def confirm_order(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = cb.from_user.id
    with SessionLocal() as s:
        order = Order(
            tg_user_id=user_id,
            username=cb.from_user.username or "",
            full_name=data["full_name"],
            phone=data["phone"],
            address=data["address"],
            comment=data.get("comment", ""),
            total=data["total"],
        )
        for pid, qty in carts[user_id].items():
            p = s.get(Product, pid)
            if not p:
                continue
            order.items.append(OrderItem(
                product_id=p.id, product_name=p.name, quantity=qty, unit_price=p.price,
            ))
        s.add(order)
        s.commit()
        order_id = order.id
    carts[user_id].clear()
    await state.clear()
    await cb.message.answer(t("order_done", user_id).format(id=order_id))
    await cb.answer()


@dp.callback_query(F.data == "cancel_order")
async def cancel_order(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(t("order_cancelled", cb.from_user.id))
    await cb.answer()


@dp.message(F.text.in_(labels("my_orders")))
async def my_orders(message: Message):
    uid = message.from_user.id
    with SessionLocal() as s:
        orders = (
            s.query(Order)
            .filter_by(tg_user_id=uid)
            .order_by(Order.id.desc())
            .limit(10)
            .all()
        )
        data = [(o.id, o.status, float(o.total), o.created_at.strftime("%d.%m.%Y %H:%M")) for o in orders]
    if not data:
        await message.answer(t("no_orders", uid))
        return
    lines = [f"#{oid} — {status} — {total:.2f} — {dt}" for oid, status, total, dt in data]
    await message.answer(t("your_orders", uid) + "\n" + "\n".join(lines), parse_mode="Markdown")


async def main():
    if not BOT_TOKEN:
        raise SystemExit("Set BOT_TOKEN in .env")
    bot = Bot(token=BOT_TOKEN)
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
