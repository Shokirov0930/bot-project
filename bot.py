import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import CommandStart

TOKEN = "8703259076:AAG7Cs5h13YvV6ywhI240m8JCC3Xndvbnos"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================
products = {}   # name -> {price, qty}
expenses = {}
sales = []      # {qty, sell_price, cost}

user_state = {}

# ================= MENU =================
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📦 Товар қўшиш"), KeyboardButton(text="💰 Сотув")],
        [KeyboardButton(text="🏬 Омбор"), KeyboardButton(text="💸 Бошқа чиқимлар")],
        [KeyboardButton(text="📊 Фойда / Зарар")],
        [KeyboardButton(text="⚙️ Обуна")],
    ],
    resize_keyboard=True
)

# ================= START =================
@dp.message(CommandStart())
async def start(message: Message):
    user_state[message.from_user.id] = None
    await message.answer("👋 Хуш келибсиз!", reply_markup=kb)

# ================= ADD PRODUCT =================
@dp.message(F.text == "📦 Товар қўшиш")
async def add_product(message: Message):
    user_state[message.from_user.id] = "add_name"
    await message.answer("📦 Товар номини ёзинг:")

# ================= SELL MENU =================
@dp.message(F.text == "💰 Сотув")
async def sell(message: Message):
    user_state[message.from_user.id] = None

    if not products:
        await message.answer("❌ Ҳали товар йўқ")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{name} ({v['qty']} дона)",
                callback_data=f"sell_{name}"
            )]
            for name, v in products.items()
        ]
    )

    await message.answer("📦 Товарни танланг:", reply_markup=keyboard)

# ================= CALLBACK SELECT PRODUCT =================
@dp.callback_query(F.data.startswith("sell_"))
async def sell_select(call: CallbackQuery):
    name = call.data.replace("sell_", "")

    user_state[call.from_user.id] = {
        "step": "sell_qty",
        "name": name
    }

    await call.message.answer(f"📊 {name}\nҚанча сотилди?")
    await call.answer()

# ================= WAREHOUSE =================
@dp.message(F.text == "🏬 Омбор")
async def warehouse(message: Message):
    user_state[message.from_user.id] = None

    if not products:
        await message.answer("🏬 Омбор бўш")
        return

    text = "🏬 ОМБОР:\n"
    for k, v in products.items():
        text += f"- {k}: {v['qty']} дона | таннарх: {v['price']} сум\n"

    await message.answer(text)

# ================= EXPENSE =================
@dp.message(F.text == "💸 Бошқа чиқимлар")
async def expense(message: Message):
    user_state[message.from_user.id] = "expense"
    await message.answer("💸 Чиқим суммасини ёзинг:")

# ================= PROFIT / LOSS =================
@dp.message(F.text == "📊 Фойда / Зарар")
async def profit(message: Message):
    total_sales = 0
    total_cost = 0
    total_profit = 0

    for s in sales:
        sale_sum = s["sell_price"] * s["qty"]
        cost_sum = s["cost"] * s["qty"]

        total_sales += sale_sum
        total_cost += cost_sum
        total_profit += (sale_sum - cost_sum)

    total_exp = sum(expenses.values()) if expenses else 0
    final_profit = total_profit - total_exp

    await message.answer(
        "📊 ҲИСОБОТ:\n\n"
        f"💰 Сотув: {total_sales} сум\n"
        f"🏷 Таннарх: {total_cost} сум\n"
        f"📈 Фойда / Зарар: {total_profit} сум\n"
        f"💸 Чиқим: {total_exp} сум\n"
        f"📊 Якуний фойда: {final_profit} сум"
    )

# ================= FLOW =================
@dp.message()
async def flow(message: Message):
    uid = message.from_user.id
    state = user_state.get(uid)

    # ---------- ADD PRODUCT ----------
    if state == "add_name":
        user_state[uid] = {"step": "price", "name": message.text}
        await message.answer("💰 Таннархни ёзинг:")
        return

    if isinstance(state, dict) and state.get("step") == "price":
        try:
            price = int(message.text)
        except:
            await message.answer("❌ Фақат рақам ёзинг")
            return

        user_state[uid] = {
            "step": "qty",
            "name": state["name"],
            "price": price
        }

        await message.answer("📦 Миқдорни ёзинг:")
        return

    if isinstance(state, dict) and state.get("step") == "qty":
        try:
            qty = int(message.text)
        except:
            await message.answer("❌ Фақат рақам ёзинг")
            return

        products[state["name"]] = {
            "price": state["price"],
            "qty": qty
        }

        user_state[uid] = None
        await message.answer("✅ Товар қўшилди")
        return

    # ---------- EXPENSE ----------
    if state == "expense":
        try:
            val = int(message.text)
        except:
            await message.answer("❌ Фақат рақам ёзинг")
            return

        expenses[len(expenses) + 1] = val
        user_state[uid] = None
        await message.answer("✅ Чиқим қўшилди")
        return

    # ---------- SELL QTY ----------
    if isinstance(state, dict) and state.get("step") == "sell_qty":
        try:
            qty = int(message.text)
        except:
            await message.answer("❌ Фақат рақам ёзинг")
            return

        name = state["name"]

        if products[name]["qty"] < qty:
            await message.answer("❌ Омборда етарли товар йўқ")
            user_state[uid] = None
            return

        user_state[uid] = {
            "step": "sell_price",
            "name": name,
            "qty": qty
        }

        await message.answer("💰 Сотув нархини ёзинг:")
        return

    # ---------- SELL PRICE ----------
    if isinstance(state, dict) and state.get("step") == "sell_price":
        try:
            sell_price = int(message.text)
        except:
            await message.answer("❌ Фақат рақам ёзинг")
            return

        name = state["name"]
        qty = state["qty"]

        cost = products[name]["price"]

        products[name]["qty"] -= qty

        sales.append({
            "qty": qty,
            "sell_price": sell_price,
            "cost": cost
        })

        profit = (sell_price - cost) * qty

        user_state[uid] = None

        await message.answer(
            f"✅ Сотув тайёр\n"
            f"📦 {name}\n"
            f"📊 {qty} дона\n"
            f"📈 Фойда: {profit}"
        )
        return

# ================= RUN =================
async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())