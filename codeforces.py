import requests
import time
import logging

def fetch_upcoming_contests():
    url = "https://codeforces.com/api/contest.list"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if data["status"] != "OK":
            raise Exception("Ошибка API: " + data.get("comment", "Неизвестная"))

        now = int(time.time())
        upcoming = [
            c for c in data['result']
            if c.get('phase') == 'BEFORE' and c.get('startTimeSeconds', 0) > now
        ]
        return upcoming
    except Exception as e:
        logging.exception("Ошибка при получении соревнований")
        raise
