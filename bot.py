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
from aiogram.client.default import DefaultBotProperties
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

# Start
@router.message(Command("start"))
async def start(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "👋 <b>Merhaba! QuotLy Bot'a hoş geldin.</b>\n\n"
        "Bir mesaja reply yaparak kullan:\n"
        "<code>/q</code> → Tek mesaj\n"
        "<code>/q2</code> → 2 mesaj\n"
        "<code>/q3</code> → 3 mesaj\n\n"
        "Renk ekle: <code>/q dark</code> veya <code>/q pink</code>",
        parse_mode="HTML"
    )

# Quote Komutu
@router.message(F.text.startswith("/q"))
async def quote_handler(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    try:
        cmd = message.text.split()[0]
        count = 1
        if len(cmd) > 2 and cmd[2:].isdigit():
            count = int(cmd[2:])

        color = "light"
        if len(message.text.split()) > 1 and message.text.split()[1] in COLORS:
            color = message.text.split()[1]

        messages = []
        current = message.reply_to_message

        if not current:
            await message.answer("❌ Lütfen bir mesaja **reply** yaparak komutu kullanın.")
            return

        for _ in range(count):
            if current:
                text = current.text or current.caption or "[Medya]"
                user = current.from_user.first_name if current.from_user else "Bilinmiyor"
                messages.append(f"“{text}”\n— {user}")
                current = current.reply_to_message
            else:
                break

        full_text = "\n\n".join(reversed(messages))

        file_path = await create_quote_image(full_text, message.from_user.first_name, color)

        await message.answer_photo(FSInputFile(file_path), caption="✨ QuotLy Bot")
        
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception:
        await message.answer("❌ Hata oluştu, tekrar deneyin.")

# ====================== ADMIN MENÜ ======================
@router.message(Command("admin"))
async def admin_menu(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Kullanıcı Listesi", callback_data="users_1")],
        [InlineKeyboardButton(text="👤 Sahibim", callback_data="owner")],
        [InlineKeyboardButton(text="📢 Kanal", callback_data="channel")],
        [InlineKeyboardButton(text="📢 Toplu Duyuru", callback_data="broadcast_start")],
    ])
    
    await message.answer("🔧 <b>Admin Paneli</b>", reply_markup=keyboard, parse_mode="HTML")

# Kullanıcı Listesi (Aktif)
@router.callback_query(F.data.startswith("users_"))
async def users_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    page = int(callback.data.split("_")[1])
    users = await get_all_users(page)
    total = await get_total_users()
    total_pages = (total + 14) // 15

    text = f"👥 <b>Toplam Kullanıcı: {total}</b>\n\n"
    for uid, username, name in users:
        uname = f"@{username}" if username else "Yok"
        text += f"<code>{uid}</code> | {uname} | {name}\n"

    keyboard = []
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="◀️", callback_data=f"users_{page-1}"))
    if page < total_pages:
        row.append(InlineKeyboardButton(text="▶️", callback_data=f"users_{page+1}"))
    if row:
        keyboard.append(row)

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

# Sahibim Butonu
@router.callback_query(F.data == "owner")
async def owner_info(callback: CallbackQuery):
    await callback.answer("Sahibim: @seninusername", show_alert=True)

# Kanal Butonu
@router.callback_query(F.data == "channel")
async def channel_info(callback: CallbackQuery):
    await callback.answer("Kanal: @seninkanal", show_alert=True)

# Toplu Duyuru
@router.callback_query(F.data == "broadcast_start")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.answer("📢 Toplu duyuru için mesajını yaz (foto, video, metin):")
    await state.set_state(BroadcastStates.waiting)

@router.message(BroadcastStates.waiting)
async def broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await message.answer("✅ Duyuru gönderiliyor... (Şu an test modunda)")

# ====================== MAIN ======================
async def main():
    await init_db()
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 QuotLy Bot Başladı! .admin komutunu dene.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
