from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import logging
import asyncio
import aiosqlite

TOKEN = "7816332278:AAEFavhg4YStZPn_-LryGEesBw3QBJyAmDc"
CHANNEL_ID = "@wan_plus"

bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMINS = [7009085528]

# Obuna tekshirish funksiyasi
async def check_subscription(user_id):
    member = await bot.get_chat_member(CHANNEL_ID, user_id)
    return member.status in ["member", "administrator", "creator"]

# /start buyrug‘i
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

    await message.answer("🎬 Salom! Kino olish uchun kod yuboring.")

# Video kodini qabul qilish
@dp.message(F.text)
async def get_video(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            "📢 Botdan foydalanish uchun kanalga obuna bo‘ling:\n"
            f"➡️ {CHANNEL_ID}\n\n"
            "✅ Obuna bo‘lgach, /start buyrug‘ini qayta kiriting."
        )
        return

    code = message.text.strip()
    async with aiosqlite.connect("videos.db") as db:
        async with db.execute("SELECT file_id FROM videos WHERE code = ?", (code,)) as cursor:
            result = await cursor.fetchone()

    if result:
        await message.answer_video(result[0])
    else:
        await message.answer("❌ Bunday kodga mos kino topilmadi!")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
