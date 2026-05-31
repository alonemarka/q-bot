import asyncio
import os
import datetime
import textwrap
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite

# ====================== AYARLAR ======================
BOT_TOKEN = "8597974338:AAEiJvJrHY-Ae4HYAZWoZky-31axSuppS9I"

ADMIN_IDS = [8773299135, 8973632679, 8230461239, 6318435017]

COLORS = {
    "light": {"bg": "#f8f9fa", "text": "#1f1f1f", "accent": "#0d6efd"},
    "dark": {"bg": "#1e1e1e", "text": "#ffffff", "accent": "#0dcaf0"},
    "pink": {"bg": "#fff0f5", "text": "#4a0033", "accent": "#ff69b4"},
    "blue": {"bg": "#e6f0ff", "text": "#002b4a", "accent": "#3498db"},
}

DB_NAME = "bot.db"

# ====================== DATABASE ======================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT
            )
        """)
        await db.commit()

async def add_user(user_id: int, username: str = None, first_name: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, joined_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, datetime.datetime.now().isoformat()))
        await db.commit()

async def get_all_users(page: int = 1, per_page: int = 15):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT user_id, username, first_name FROM users 
            ORDER BY joined_at DESC LIMIT ? OFFSET ?
        """, (per_page, offset)) as cursor:
            return await cursor.fetchall()

async def get_total_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            result = await cursor.fetchone()
            return result[0]

# ====================== QUOTE GENERATOR ======================
async def create_quote_image(message_text: str, username: str, color: str = "light"):
    colors = COLORS.get(color, COLORS["light"])
    width, height = 850, 520
    image = Image.new("RGB", (width, height), color=colors["bg"])
    draw = ImageDraw.Draw(image)

    try:
        font_large = ImageFont.truetype("arial.ttf", 42)
        font_small = ImageFont.truetype("arial.ttf", 30)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    wrapped = textwrap.fill(message_text, width=38)

    draw.text((70, 80), wrapped, fill=colors["text"], font=font_large, spacing=8)
    draw.text((70, 380), f"— {username}", fill=colors["accent"], font=font_small)
    draw.rectangle([30, 30, width-30, height-30], outline=colors["accent"], width=6)

    path = f"quote_{username}_{color}.png"
    image.save(path)
    return path

# ====================== BOT ======================
router = Router()

class BroadcastStates(StatesGroup):
    waiting = State()

# Karşılama Mesajı
@router.message(Command("start"))
async def start(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "👋 Merhaba! QuotLy Bot'a hoş geldin.\n\n"
        "Bir mesaja reply yaparak:\n"
        "• `/q` → Tek mesaj quote\n"
        "• `/q2` → Son 2 mesaj quote\n"
        "• `/q3` → Son 3 mesaj quote\n\n"
        "Adminler `.admin` yazabilir."
    )

# Quote Komutu (/q, /q2, /q3 ...)
@router.message(F.text.startswith("/q"))
async def quote_handler(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    try:
        # Kaç mesaj alınacağını belirle (/q2 → 2)
        command = message.text.split()[0]
        count = 1
        if len(command) > 2 and command[2:].isdigit():
            count = int(command[2:])

        color = "light"
        if len(message.text.split()) > 1:
            arg = message.text.split()[1]
            if arg in COLORS:
                color = arg

        # Mesajları topla
        messages = []
        current = message.reply_to_message if message.reply_to_message else message

        for _ in range(count):
            if current:
                text = current.text or current.caption or "Medya içeriği"
                user = current.from_user.first_name
                messages.append(f"“{text}”\n— {user}")
                # Bir önceki mesaja git (grup için)
                if current.reply_to_message:
                    current = current.reply_to_message
                else:
                    break

        full_text = "\n\n".join(reversed(messages))

        file_path = await create_quote_image(
            message_text=full_text,
            username=message.from_user.first_name,
            color=color
        )

        await message.answer_photo(
            photo=FSInputFile(file_path),
            caption="✨ QuotLy Bot"
        )

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await message.answer("❌ Bir hata oluştu. Tekrar deneyin.")

# Admin Menüsü
@router.message(Command("admin"))
async def admin_menu(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Kullanıcı Listesi", callback_data="users_1")],
        [InlineKeyboardButton(text="📢 Toplu Duyuru", callback_data="broadcast_start")],
    ])
    
    await message.answer("🔧 **Admin Paneli**", reply_markup=keyboard, parse_mode="Markdown")

# Diğer admin fonksiyonları (kısaca)
@router.callback_query(F.data.startswith("users_"))
async def users_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer("Kullanıcı listesi yakında eklenecek.")

@router.callback_query(F.data == "broadcast_start")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.answer("📢 Toplu duyuru için mesaj yazın:")
    await state.set_state(BroadcastStates.waiting)

@router.message(BroadcastStates.waiting)
async def broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await message.answer("Toplu duyuru özelliği şu an devre dışı.")

# ====================== MAIN ======================
async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 QuotLy Bot Başladı! /start yazmayı dene.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
