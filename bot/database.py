import aiosqlite
import datetime

DB_NAME = "bot.db"

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
