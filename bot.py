import json
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

USERS_FILE = "users.json"
CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"subscribers": [], "participants": {}}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

def add_user(user_id):
    data = load_users()
    if user_id not in data["subscribers"]:
        data["subscribers"].append(user_id)
    save_users(data)

def remove_user(user_id):
    data = load_users()
    if user_id in data["subscribers"]:
        data["subscribers"].remove(user_id)
    save_users(data)

def add_participant(user_id, contest_id):
    data = load_users()
    cid = str(contest_id)
    if cid not in data["participants"]:
        data["participants"][cid] = []
    if user_id not in data["participants"][cid]:
        data["participants"][cid].append(user_id)
    save_users(data)

def get_participants(contest_id):
    data = load_users()
    return data.get("participants", {}).get(str(contest_id), [])

async def start_cmd(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📬 Подписаться", callback_data="subscribe")
    kb.button(text="📪 Отписаться", callback_data="unsubscribe")
    kb.button(text="📅 Список соревнований", callback_data="upcoming")
    await message.answer("Выберите действие:", reply_markup=kb.as_markup())

async def handle_callback(callback: types.CallbackQuery, bot: Bot):
    from codeforces import fetch_upcoming_contests

    uid = callback.from_user.id
    data = callback.data

    try:
        if data == "subscribe":
            add_user(uid)
            await callback.message.edit_text("✅ Подписка оформлена.")
        elif data == "unsubscribe":
            remove_user(uid)
            await callback.message.edit_text("❌ Подписка отменена.")
        elif data == "upcoming":
            contests = fetch_upcoming_contests()[:5]
            for c in contests:
                name = c["name"]
                start = c["startTimeSeconds"]
                cid = c["id"]
                dt = datetime.fromtimestamp(start)
                join_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Участвовать", callback_data=f"join_{cid}")]
                ])
                await callback.message.answer(f"<b>{name}</b>\n🕒 Начало: {dt}", parse_mode=ParseMode.HTML, reply_markup=join_kb)
        elif data.startswith("join_"):
            cid = int(data.split("_")[1])
            add_participant(uid, cid)
            await callback.message.edit_text("🎯 Участие подтверждено!")
    except Exception as e:
        logging.exception("Ошибка при обработке кнопки")
        await callback.message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

def setup_bot():
    config = load_config()
    bot = Bot(token=config["telegram_token"])
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_cmd, CommandStart())
    dp.callback_query.register(handle_callback, F.data)

    return bot, dp

def get_app():
    config = load_config()
    bot = Bot(token=config["telegram_token"])
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_cmd, CommandStart())
    dp.callback_query.register(handle_callback, F.data)

    return bot, dp
