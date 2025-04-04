import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

# Bot tokeni va kanallar ID'lari
TOKEN = "7816332278:AAFPJXE17yrRShRhplZqDeCI6EbEuXVAwCE"  # <--- o'z tokeningizni kiriting
CHANNEL_IDS = [
    "@wan_plus",  # 1-kanal
    # "@channel2_id",  # 2-kanal
    # "@channel3_id",  # 3-kanal
    # "@channel4_id",  # 4-kanal
    # "@channel5_id",  # 5-kanal
    # "@channel6_id",  # 6-kanal
    # "@channel7_id",  # 7-kanal
]
ADMINS = [7009085528]

# Botni yaratish (HTML parse_mode bilan)
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Baza tayyorlash
async def setup_db():
    async with aiosqlite.connect("videos.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                code TEXT PRIMARY KEY,
                file_id TEXT
            )
        """)
        await db.commit()

# Obuna tekshiruvi (bir nechta kanal uchun)
async def check_subscription(user_id):
    for channel_id in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True
        except TelegramBadRequest:
            continue  # Agar kanal topilmasa yoki xatolik bo'lsa, keyingi kanalni tekshiramiz
    return False

# Inline tugma uchun keyboard
def get_check_subscription_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_subscription")]
    ])
    return keyboard

# /start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        channels_list = "\n".join([f"➡️ {i+1} - {channel}" for i, channel in enumerate(CHANNEL_IDS)])
        await message.answer(
            f"📢 Botdan foydalanish uchun quyidagi kanallardan biriga obuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing yoki /start ni qayta yuboring.",
            reply_markup=get_check_subscription_keyboard()
        )
        return
    await message.answer("🎬 Tabriklaymiz botdan foydalanishingiz mumkin")

# Obuna tekshiruvi callback
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
            f"📢 Siz hali kanallarga obuna emassiz! Iltimos, quyidagi kanallardan biriga obuna bo'ling:\n{channels_list}\n\n"
            "✅ Obuna bo'lgach, <b>Tekshirish</b> tugmasini bosing.",
            reply_markup=get_check_subscription_keyboard()
        )

# /help buyrug'i
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🆘 <b>Yordam:</b>\n"
        "📥 Kodni yuboring — agar mavjud bo'lsa, video fayl yuboriladi.\n"
        "👮 Admin bo'lsangiz, reply orqali video faylga kod yozib yuboring.\n"
        "🔐 Foydalanish uchun kamida bitta kanalga obuna bo'lish shart."
    )

# Kodni qayta ishlash (video qidirish yoki qo'shish)
@dp.message()
async def handle_message(message: types.Message):
    code = message.text.strip()

    # Admin video qo'shmoqda
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

    # Oddiy foydalanuvchi — kod orqali qidirish
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

# Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await setup_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())