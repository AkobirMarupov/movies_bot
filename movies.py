import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiohttp import web
import os

# Bot tokeni va kanallar ID'lari
TOKEN = os.getenv("7816332278:AAGAVGH8OLJ7b74hsSlYMq2qrs49EcDMYYw")  # Render’da BOT_TOKEN o‘rnatilgan bo‘lishi kerak
CHANNEL_IDS = ["@wan_plus"]
ADMINS = [7009085528]


bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


async def setup_db():
    async with aiosqlite.connect("videos.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                code TEXT PRIMARY KEY,
                file_id TEXT
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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_subscription")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        channels_list = "\n".join([f"➡️ {i+1} - {channel}" for i, channel in enumerate(CHANNEL_IDS)])
        await message.answer(
            f"📢 Botdan foydalanish uchun quyidagi kanalgavobuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing yoki /start ni qayta yuboring.",
            reply_markup=get_check_subscription_keyboard()
        )
        return
    await message.answer("🎬 Tabriklaymiz botdan foydalanishingiz mumkin")

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
            f"📢 Siz hali kanallarga obuna emassiz! Iltimos, quyidagi kanalga obuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing.",
            reply_markup=get_check_subscription_keyboard()
        )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🆘 <b>Yordam:</b>\n"
        "📥 Kodni yuboring — agar mavjud bo'lsa, video fayl yuboriladi.\n"
        "👮 Admin bo'lsangiz, reply orqali video faylga kod yozib yuboring.\n"
        "🔐 Foydalanish uchun kamida bitta kanalga obuna bo'lish shart."
    )

@dp.message()
async def handle_message(message: types.Message):
    code = message.text.strip()
    if message.from_user.id in ADMINS and message.reply_to_message and message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        async with aiosqlite.connect("videos.db") as db:
            try:
                await db.execute("INSERT INTO videos (code, file_id) VALUES (?, ?)", (code, file_id))
                await db.commit()
                await message.answer(f"✅ Video saqlandi! Kod: <code>{code}</code>")
            except aiosqlite.IntegrityError:
                await message.answer("⚠️ Bu kod allaqachon mavjud!")
        return

    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        channels_list = "\n".join([f"➡️ {i+1} - {channel}" for i, channel in enumerate(CHANNEL_IDS)])
        await message.answer(
            f"📢 Botdan foydalanish uchun quyidagi kanallardan biriga obuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing yoki /start ni qayta yuboring.",
            reply_markup=get_check_subscription_keyboard()
        )
        return

    async with aiosqlite.connect("videos.db") as db:
        async with db.execute("SELECT file_id FROM videos WHERE code = ?", (code,)) as cursor:
            result = await cursor.fetchone()

    if result:
        await message.answer_video(result[0])
    else:
        await message.answer("❌ Bunday kodga mos video topilmadi.")


async def handle_root(request):
    return web.Response(text="Bot is alive!")


async def start_bot_and_server():

    await setup_db()
    asyncio.create_task(dp.start_polling(bot))


    app = web.Application()
    app.add_routes([web.get('/', handle_root)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_bot_and_server())