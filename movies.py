from fastapi import FastAPI
import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiosqlite

TOKEN = "7816332278:AAFPJXE17yrRShRhplZqDeCI6EbEuXVAwCE"
CHANNEL_ID = "@wan_plus"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()  # FastAPI serverini yaratamiz

ADMINS = [7009085528]

async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def setup_db():
    async with aiosqlite.connect("videos.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS videos (code TEXT PRIMARY KEY, file_id TEXT)")
        await db.commit()

@dp.message(Command("start"))
async def start(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            "📢 Botdan foydalanish uchun kanalga obuna bo‘ling:\n"
            f"➡️ {CHANNEL_ID}\n\n"
            "✅ Obuna bo‘lgach, /start buyrug‘ini qayta kiriting."
        )
        return
    await message.answer("🎬 Salom! Kino olish uchun kodni yuboring.")

@dp.message(types.Message)
async def add_or_get_video(message: types.Message):
    code = message.text.strip()

    if message.from_user.id in ADMINS and message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        async with aiosqlite.connect("videos.db") as db:
            try:
                await db.execute("INSERT INTO videos (code, file_id) VALUES (?, ?)", (code, file_id))
                await db.commit()
                await message.answer(f"✅ Kino qo‘shildi! Kod: {code}")
            except aiosqlite.IntegrityError:
                await message.answer("⚠️ Bu kod allaqachon mavjud!")
        return

    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            "📢 Botdan foydalanish uchun kanalga obuna bo‘ling:\n"
            f"➡️ {CHANNEL_ID}\n\n"
            "✅ Obuna bo‘lgach, /start buyrug‘ini qayta kiriting."
        )
        return

    async with aiosqlite.connect("videos.db") as db:
        async with db.execute("SELECT file_id FROM videos WHERE code = ?", (code,)) as cursor:
            result = await cursor.fetchone()

    if result:
        await message.answer_video(result[0])
    else:
        await message.answer("❌ Bunday kodga mos kino topilmadi!")

async def bot_runner():
    logging.basicConfig(level=logging.INFO)
    await setup_db()  # Bazani tayyorlash
    await dp.start_polling(bot)

# FastAPI endpoint (bu yerga UptimeRobot har 5 daqiqada so‘rov yuboradi)
@app.get("/")
async def root():
    return {"message": "Bot is running!"}

# Botni va serverni ishga tushirish
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(bot_runner())  # Botni fon rejimida ishga tushiramiz
    uvicorn.run(app, host="0.0.0.0", port=8000)  # FastAPI serverini ishga tushiramiz
