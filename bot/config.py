import os
from dotenv import load_dotenv

load_dotenv()

# ✅ DOĞRU ŞEKİL
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin ID'lerin (istediğin kadar ekleyebilirsin)
ADMIN_IDS = [8773299135, 8973632679, 8230461239, 6318435017]

COLORS = {
    "light": {"bg": "#f8f9fa", "text": "#1f1f1f", "accent": "#0d6efd"},
    "dark": {"bg": "#1e1e1e", "text": "#ffffff", "accent": "#0dcaf0"},
    "pink": {"bg": "#fff0f5", "text": "#4a0033", "accent": "#ff69b4"},
    "blue": {"bg": "#e6f0ff", "text": "#002b4a", "accent": "#3498db"},
}
