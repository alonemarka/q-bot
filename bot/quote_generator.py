from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
from bot.config import COLORS

async def create_quote_image(message_text: str, username: str, color: str = "light"):
    colors = COLORS.get(color, COLORS["light"])
    bg_color = colors["bg"]
    text_color = colors["text"]
    accent = colors["accent"]

    width, height = 850, 520
    image = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)

    try:
        font_large = ImageFont.truetype("arial.ttf", 42)
        font_small = ImageFont.truetype("arial.ttf", 30)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    wrapped = textwrap.fill(message_text, width=38)

    draw.text((70, 80), wrapped, fill=text_color, font=font_large, spacing=8)
    draw.text((70, 380), f"— {username}", fill=accent, font=font_small)

    draw.rectangle([30, 30, width-30, height-30], outline=accent, width=6)

    path = f"quote_{username}_{color}.png"
    image.save(path)
    return path
