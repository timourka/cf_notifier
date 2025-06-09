import asyncio
import time
import json
import logging
from datetime import datetime, timedelta

from codeforces import fetch_upcoming_contests
from bot import get_app, load_users

CONTESTS_FILE = "contests.json"
LOG_FILE = "log.txt"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def load_known_contests():
    try:
        with open(CONTESTS_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_known_contests(contest_ids):
    with open(CONTESTS_FILE, "w") as f:
        json.dump(list(contest_ids), f)

async def notify_users(bot, user_ids, text):
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            logging.info(f"Уведомление отправлено пользователю {uid}")
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение пользователю {uid}: {e}")

async def notify_loop(bot):
    known = load_known_contests()
    while True:
        try:
            contests = fetch_upcoming_contests()
            now = int(time.time())

            # Новые соревнования
            new_contests = [c for c in contests if c['id'] not in known]
            for c in new_contests:
                start = datetime.fromtimestamp(c['startTimeSeconds']).strftime('%Y-%m-%d %H:%M')
                msg = f"🆕 Новое соревнование: {c['name']}\n🕒 Стартует: {start}"
                subs = load_users().get("subscribers", [])
                await notify_users(bot, subs, msg)
                known.add(c['id'])

            # Напоминания
            for c in contests:
                delta = c['startTimeSeconds'] - now
                cid = c['id']
                start_str = datetime.fromtimestamp(c['startTimeSeconds']).strftime('%H:%M %d.%m')
                participants = load_users().get("participants", {}).get(str(cid), [])
                if not participants:
                    continue

                if 0 < delta <= 1800:
                    await notify_users(bot, participants, f"⚠️ '{c['name']}' начнётся менее чем через 30 минут ({start_str})")
                elif 1800 < delta <= 3600:
                    await notify_users(bot, participants, f"⏰ Через 1 час начнётся: {c['name']}")
                elif 3600 < delta <= 7200:
                    await notify_users(bot, participants, f"⏰ Через 2 часа начнётся: {c['name']}")
                elif datetime.fromtimestamp(c['startTimeSeconds']).date() == datetime.now().date():
                    await notify_users(bot, participants, f"📅 Сегодня в {start_str} начнётся: {c['name']}")
                elif datetime.fromtimestamp(c['startTimeSeconds']).date() == (datetime.now() + timedelta(days=1)).date():
                    await notify_users(bot, participants, f"📅 Завтра в {start_str} начнётся: {c['name']}")

            save_known_contests(known)

        except Exception as e:
            logging.exception("Ошибка в цикле уведомлений")

        await asyncio.sleep(1800)  # Пауза 30 мин

async def main():
    try:
        logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

        app, dp = get_app()
        bot = app

        logging.info("Запуск бота и цикла уведомлений...")

        # Параллельно запускаем бота и основной цикл
        await asyncio.gather(
            dp.start_polling(bot),
            notify_loop(bot)
        )
    except Exception:
        logging.exception("Фатальная ошибка в main()")

if __name__ == "__main__":
    asyncio.run(main())
