# Movies Telegram Bot

## 📌 About
This is a Telegram bot that allows users to retrieve movies by entering a unique movie code. The bot checks whether the user is subscribed to a specific Telegram channel before providing access to the movies. It uses the `aiogram` library for handling Telegram bot interactions and `aiosqlite` for storing movie codes and corresponding video file IDs in a SQLite database.

## ⚙️ Features
- ✅ **Subscription Check**: Ensures that the user is subscribed to `@wan_plus` before using the bot.
- 🎬 **Retrieve Movies**: Users can enter a code to receive the corresponding movie.
- 📂 **Database Support**: Uses SQLite to store and retrieve movie codes and video file IDs.
- 🔄 **Asynchronous Processing**: Uses `asyncio` for efficient, non-blocking execution.

## 🚀 Installation & Setup
### 1️⃣ Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Required dependencies (`aiogram`, `aiosqlite`)

### 2️⃣ Clone the Repository
```sh
 git clone https://github.com/AkobirMarupov/movies-bot.git
 cd movies-bot
```

### 3️⃣ Install Dependencies
```sh
pip install aiogram aiosqlite
```

### 4️⃣ Configure the Bot
Edit the `TOKEN` and `CHANNEL_ID` values in the script:
```python
TOKEN = "your-bot-token-here"
CHANNEL_ID = "@your-channel-name"
```

### 5️⃣ Run the Bot
```sh
python bot.py
```

## 📜 Code Explanation

### 1️⃣ Importing Required Libraries
```python
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import logging
import asyncio
import aiosqlite
```
- `aiogram`: Handles Telegram bot interactions.
- `asyncio`: Manages asynchronous execution.
- `aiosqlite`: Provides async support for SQLite database operations.

### 2️⃣ Bot Initialization
```python
TOKEN = "your-bot-token"
CHANNEL_ID = "@your-channel"
bot = Bot(token=TOKEN)
dp = Dispatcher()
ADMINS = [123456789]  # List of admin user IDs
```
- Initializes the bot with the provided token.
- Defines the target channel for subscription checking.

### 3️⃣ Subscription Check Function
```python
async def check_subscription(user_id):
    member = await bot.get_chat_member(CHANNEL_ID, user_id)
    return member.status in ["member", "administrator", "creator"]
```
- Checks if a user is subscribed to the required channel.

### 4️⃣ Start Command Handler
```python
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
```
- If the user is not subscribed, they are prompted to subscribe first.
- If subscribed, they can enter a movie code.

### 5️⃣ Handling Movie Code Requests
```python
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
```
- Queries the SQLite database to retrieve the video associated with the entered code.
- If the code exists, the bot sends the corresponding video file.
- If the code is invalid, the bot notifies the user.

### 6️⃣ Running the Bot
```python
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```
- Initializes logging and starts polling to receive messages.

## 📂 Database Schema
The SQLite database `videos.db` should contain a table named `videos`:
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    file_id TEXT NOT NULL
);
```
- `code`: Unique identifier for each movie.
- `file_id`: Telegram file ID of the movie.

## 📢 Future Improvements
- ✅ **Admin Panel**: Allow admins to add/remove movies via bot commands.
- 🔍 **Search Feature**: Users can search for movies by name.
- 📊 **Statistics**: Track the number of requests per movie.

## 📜 License
This project is open-source and available under the MIT License.

---

🎬 Enjoy using the Movies Telegram Bot!

