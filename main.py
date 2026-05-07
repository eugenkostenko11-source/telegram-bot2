import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

ADMINS = [5219477547]

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/Help"), KeyboardButton(text="/Me")],
        [KeyboardButton(text="/joke"), KeyboardButton(text="/quote")],
        [KeyboardButton(text="/story")]
    ],
    resize_keyboard=True
)

contact_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🆘 Звернутися за підтримкою", callback_data="contact_admin")]
    ]
)

class ContactAdmin(StatesGroup):
    waiting_for_message = State()

async def ask_ai(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-r1-0528",
        "messages": [
            {
                "role": "system",
                "content": "Відповідай грубо. Не використовуй форматування типу **, *, __, markdown. Не пояснюй правила. Просто відповідай."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 512
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, headers=headers, json=payload) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("AI error:", e)
        return "❌ Помилка AI"

@dp.message(Command("start"))
async def start_cmd(message: Message):
    user = message.from_user
    username = user.username or "Невідомий"
    await message.answer(
        f"Привіт, {username}! 👋\n\n"
        "Я AI-помічник для тексту, відповідей і простих пояснень.\n\n"
        "Що я вмію:\n"
        "📝 Писати тексти, повідомлення, історії та ідеї\n"
        "💡 Відповідати на питання\n"
        "🔍 Пояснювати складні речі простими словами\n"
        "🆘 Передавати повідомлення адміну через кнопку підтримки\n\n"
        "Натисни кнопку нижче або напиши команду.",
        reply_markup=main_kb
    )

@dp.message(Command("Help"))
async def help_cmd(message: Message):
    await message.answer(
        "📘 Допомога\n\n"
        "Команди бота:\n"
        "/start — запуск бота\n"
        "/Help — список можливостей\n"
        "/Me — інформація про користувача\n"
        "/ai — запит до AI\n"
        "/joke — випадковий жарт\n"
        "/quote — мотиваційна цитата\n"
        "/story — коротка історія\n\n"
        "Також є кнопка для звернення до адміністратора.",
        reply_markup=contact_kb
    )

@dp.message(Command("Me"))
async def me_cmd(message: Message):
    user = message.from_user
    username = user.username or "Невідомий"
    await message.answer(
        f"🔍 Твоя інформація:\n"
        f"📛 Username: @{username}\n"
        f"👤 Імʼя: {user.first_name}\n"
        f"🆔 ID: {user.id}"
    )

@dp.message(Command("joke"))
async def joke_cmd(message: Message):
    answer = await ask_ai("Розкажи короткий веселий жарт українською мовою.")
    await message.answer(answer)

@dp.message(Command("quote"))
async def quote_cmd(message: Message):
    answer = await ask_ai("Напиши коротку мотиваційну або надихаючу цитату українською мовою.")
    await message.answer(answer)

@dp.message(Command("story"))
async def story_cmd(message: Message):
    answer = await ask_ai("Напиши коротку цікаву історію українською мовою на 3-4 речення.")
    await message.answer(answer)

@dp.callback_query(lambda c: c.data == "contact_admin")
async def ask_user_message(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Напишіть повідомлення, яке я передам адміністратору.")
    await state.set_state(ContactAdmin.waiting_for_message)
    await callback.answer()

@dp.message(ContactAdmin.waiting_for_message)
async def send_to_admin(message: Message, state: FSMContext):
    user = message.from_user
    username = f"@{user.username}" if user.username else "Немає username"
    text = (
        f"🆘 Нове звернення до адміна\n\n"
        f"👤 Імʼя: {user.first_name}\n"
        f"📛 Username: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💬 Повідомлення:\n{message.text or ''}"
    )

    for admin_id in ADMINS:
        await bot.send_message(admin_id, text)

    await message.answer("✅ Повідомлення відправлено адміну.")
    await state.clear()

@dp.message()
async def handle_message(message: Message):
    text = message.text or ""
    bot_user = await bot.get_me()

    if text.startswith("/"):
        return

    if (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == bot_user.id
    ):
        answer = await ask_ai(text)
        await message.answer(answer)
        return

    answer = await ask_ai(text)
    await message.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())