import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from .quote_generator import create_quote_image
from .database import add_user, get_all_users, get_total_users
from bot.config import ADMIN_IDS, COLORS

router = Router()

class BroadcastStates(StatesGroup):
    waiting = State()

# Quote Komutu
@router.message(F.reply_to_message, F.text.startswith("/q"))
async def quote_handler(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    target = message.reply_to_message
    color = "light"
    args = message.text.split()
    if len(args) > 1 and args[1] in COLORS:
        color = args[1]

    file_path = await create_quote_image(
        message_text=target.text or target.caption or "Medya içeriği",
        username=target.from_user.first_name,
        color=color
    )

    await message.answer_photo(
        photo=FSInputFile(file_path),
        caption="✨ QuotLy Bot"
    )
    
    if os.path.exists(file_path):
        os.remove(file_path)

# Admin Menü
@router.message(Command("admin"))
async def admin_menu(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Kullanıcı Listesi", callback_data="users_1")],
        [InlineKeyboardButton(text="📢 Toplu Duyuru", callback_data="broadcast_start")],
    ])
    
    await message.answer("🔧 **Admin Paneli**", reply_markup=keyboard, parse_mode="Markdown")

# Kullanıcı Listesi
@router.callback_query(F.data.startswith("users_"))
async def users_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    page = int(callback.data.split("_")[1])
    users = await get_all_users(page)
    total = await get_total_users()
    total_pages = (total + 14) // 15

    text = f"**Toplam Kullanıcı: {total}**\n\n"
    for uid, username, name in users:
        uname = f"@{username}" if username else "Yok"
        text += f"`{uid}` | {uname} | {name}\n"

    keyboard = []
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="◀️", callback_data=f"users_{page-1}"))
    if page < total_pages:
        row.append(InlineKeyboardButton(text="▶️", callback_data=f"users_{page+1}"))
    if row:
        keyboard.append(row)

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

# Toplu Duyuru
@router.callback_query(F.data == "broadcast_start")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.answer("📢 **Toplu duyuru için mesajınızı yazın** (foto, video, metin):")
    await state.set_state(BroadcastStates.waiting)

@router.message(BroadcastStates.waiting)
async def broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await message.answer("✅ Duyuru gönderiliyor...")

    users = []
    page = 1
    while True:
        batch = await get_all_users(page, 50)
        if not batch:
            break
        users.extend([u[0] for u in batch])
        page += 1

    success = 0
    for user_id in users:
        try:
            if message.text:
                await message.bot.send_message(user_id, message.text)
            elif message.photo:
                await message.bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await message.bot.send_video(user_id, message.video.file_id, caption=message.caption)
            success += 1
        except:
            continue

    await message.answer(f"✅ Duyuru **{success}** kullanıcıya başarıyla gönderildi.")
