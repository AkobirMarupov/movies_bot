import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_IDS = ["@marupov_akobir"]
ADMINS = [7009085528]

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def setup_db():
    async with aiosqlite.connect("videos.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                code TEXT PRIMARY KEY,
                file_id TEXT,
                description TEXT
            )
        """)
        await db.commit()

async def check_subscription(user_id):
    for channel_id in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True
        except TelegramBadRequest:
            continue
    return False

def get_check_subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_subscription")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        channels_list = "\n".join([f"➡️ {i+1} - {channel}" for i, channel in enumerate(CHANNEL_IDS)])
        await message.answer(
            f"📢 Botdan foydalanish uchun quyidagi kanalga obuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing yoki /start ni qayta yuboring.",
            reply_markup=get_check_subscription_keyboard()
        )
        return
    await message.answer("🎥 Tabriklaymiz! Botdan foydalanishingiz mumkin.")

@dp.callback_query(lambda c: c.data == "check_subscription")
async def process_check_subscription(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    is_subscribed = await check_subscription(callback_query.from_user.id)
    if is_subscribed:
        await bot.send_message(
            callback_query.from_user.id,
            "✅ Obuna tasdiqlandi! Endi kodni yuboring va video faylni oling.\nYordam: /help"
        )
    else:
        channels_list = "\n".join([f"➡️ {i+1} - {channel}" for i, channel in enumerate(CHANNEL_IDS)])
        await bot.send_message(
            callback_query.from_user.id,
            f"📢 Siz hali kanallarga obuna emassiz! Iltimos, quyidagilarga obuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing.",
            reply_markup=get_check_subscription_keyboard()
        )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🕘 <b>Yordam:</b>\n"
        "🗕 Kodni yuboring — agar mavjud bo'lsa, video fayl yuboriladi.\n"
        "👮 Admin bo'lsangiz, reply orqali video faylga quyidagi formatda tavsif yozib yuboring:\n"
        "<code>Kod | Kino nomi | Til | Format</code>\n"
        "🔐 Foydalanish uchun kamida bitta kanalga obuna bo'lish shart."
    )

@dp.message()
async def handle_message(message: types.Message):
    code = message.text.strip()

    if message.from_user.id in ADMINS and message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        parts = code.split("|")
        if len(parts) != 4:
            await message.answer("⚠️ Format noto'g'ri. To'g'ri format:\n<code>Kod | Kino nomi | Til | Format</code>")
            return

        kod = parts[0].strip()
        name = parts[1].strip()
        lang = parts[2].strip()
        quality = parts[3].strip()

        description = (
            f"🎬 Kino nomi: {name}\n"
            f"🌐 Til: {lang}\n"
            f"📟️ Format: {quality}\n"
            f"📢 Kanalimiz: {CHANNEL_IDS[0]}"
        )

        try:
            async with aiosqlite.connect("videos.db") as db:
                await db.execute("INSERT INTO videos (code, file_id, description) VALUES (?, ?, ?)", (kod, file_id, description))
                await db.commit()
                await message.answer(f"✅ Video saqlandi!\n{description}")
        except aiosqlite.IntegrityError:
            await message.answer("⚠️ Bu kod allaqachon mavjud!")
        return

    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        channels_list = "\n".join([f"➡️ {i+1} - {channel}" for i, channel in enumerate(CHANNEL_IDS)])
        await message.answer(
            f"📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing yoki /start ni qayta yuboring.",
            reply_markup=get_check_subscription_keyboard()
        )
        return

    async with aiosqlite.connect("videos.db") as db:
        async with db.execute("SELECT file_id, description FROM videos WHERE code = ?", (code,)) as cursor:
            result = await cursor.fetchone()

    if result:
        file_id, description = result
        await message.answer_video(video=file_id, caption=description)
    else:
        await message.answer("❌ Bunday kodga mos video topilmadi.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(setup_db())
    asyncio.run(dp.start_polling(bot))