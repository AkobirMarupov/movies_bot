from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import logging
import asyncio
import aiosqlite

TOKEN = "7816332278:AAFPJXE17yrRShRhplZqDeCI6EbEuXVAwCE"
CHANNEL_ID = "@wan_plus"

# Bot va dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Adminlar ro‘yxati
ADMINS = [7009085528]  # O'zingizning Telegram ID'ingizni qo‘shing

# **Obuna tekshirish funksiyasi**
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False  # Agar kanal mavjud bo‘lmasa yoki botda ruxsat bo‘lmasa

# **Botni ishga tushirishda bazani yaratish**
async def setup_db():
    async with aiosqlite.connect("videos.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS videos (code TEXT PRIMARY KEY, file_id TEXT)")
        await db.commit()

# **/start buyrug‘i**
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

# **Video qo‘shish (adminlar uchun)**
@dp.message(F.text)
async def add_or_get_video(message: types.Message):
    code = message.text.strip()

    # **Admin bo‘lsa va videoga javob bersa, uni bazaga qo‘shadi**
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

    # **Oddiy foydalanuvchilar kod yuborsa, video topish**
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

# **Botni ishga tushirish**
async def main():
    logging.basicConfig(level=logging.INFO)
    await setup_db()  # Bazani tayyorlash
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
