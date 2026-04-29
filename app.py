import os, asyncio, sqlite3, json
from datetime import datetime, date

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, MenuButtonWebApp

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

# ---------- КОНФИГ (вшито) ----------
TOKEN = "8656839032:AAETcA3tgSxzaJccaAuKVsL1MXxqfO5VNks"
APP_URL = "https://introcookie.github.io/epstein-bot"

# ---------- БАЗА ----------
DB = "epstein.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                last_daily DATE DEFAULT '2000-01-01'
            )
        """)
init_db()

def get_user(user_id: int):
    with sqlite3.connect(DB) as conn:
        row = conn.execute("SELECT balance, last_daily FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row:
            return {"balance": row[0], "last_daily": row[1]}
        conn.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return {"balance": 0, "last_daily": "2000-01-01"}

def update_balance(user_id: int, delta: int):
    with sqlite3.connect(DB) as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id))
        conn.commit()
        return conn.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()[0]

def set_username(user_id: int, username: str):
    with sqlite3.connect(DB) as conn:
        conn.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
        conn.commit()

def set_last_daily(user_id: int, dt: str):
    with sqlite3.connect(DB) as conn:
        conn.execute("UPDATE users SET last_daily=? WHERE user_id=?", (dt, user_id))
        conn.commit()

def get_top(limit=10):
    with sqlite3.connect(DB) as conn:
        rows = conn.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,)).fetchall()
        return [{"user_id": r[0], "username": r[1] or str(r[0]), "balance": r[2]} for r in rows]

# ---------- БОТ ----------
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(msg: types.Message):
    user = msg.from_user
    set_username(user.id, user.username or user.first_name)
    await bot.set_chat_menu_button(
        chat_id=msg.chat.id,
        menu_button=MenuButtonWebApp(
            text="🔥 Кликер",
            web_app=WebAppInfo(url=f"{APP_URL}/static/index.html")
        )
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎮 Играть", web_app=WebAppInfo(url=f"{APP_URL}/static/index.html"))]
    ])
    await msg.answer(
        "Привет! Ты попал на остров Эпштейна. Скорее кликай кнопку! 🔥",
        reply_markup=kb
    )

# ---------- FASTAPI ----------
app_fastapi = FastAPI()
# Статику не монтируем, она на GitHub Pages

@app_fastapi.get("/api/balance")
async def api_balance(user_id: int):
    ud = get_user(user_id)
    return {"balance": ud["balance"], "last_daily": ud["last_daily"]}

@app_fastapi.post("/api/click")
async def api_click(req: Request):
    data = await req.json()
    user_id = data["user_id"]
    count = data["count"]
    balance = update_balance(user_id, count)
    return {"balance": balance}

@app_fastapi.get("/api/top")
async def api_top():
    return get_top()

@app_fastapi.post("/api/buy_booster")
async def api_buy(req: Request):
    data = await req.json()
    user_id = data["user_id"]
    cost = data["cost"]
    user = get_user(user_id)
    if user["balance"] < cost:
        return {"success": False, "message": "Не хватает монет"}
    new_balance = update_balance(user_id, -cost)
    return {"success": True, "balance": new_balance}

@app_fastapi.post("/api/daily")
async def api_daily(req: Request):
    data = await req.json()
    user_id = data["user_id"]
    user = get_user(user_id)
    today = date.today().isoformat()
    if user["last_daily"] == today:
        return {"success": False, "message": "Сегодня уже забирал, бро"}
    set_last_daily(user_id, today)
    new_balance = update_balance(user_id, 50)
    return {"success": True, "balance": new_balance, "bonus": 50}

async def run_bot():
    await dp.start_polling(bot)

@app_fastapi.on_event("startup")
async def on_startup():
    asyncio.create_task(run_bot())

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    uvicorn.run(app_fastapi, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))