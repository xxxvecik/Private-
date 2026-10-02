"""Отправляет праздники за сегодня в Telegram. Запускается из GitHub Actions."""
import datetime as dt
import os
import re
import sys
from zoneinfo import ZoneInfo

import httpx

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TZ = ZoneInfo("Europe/Berlin")

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def fetch_holidays(day: int, month: int) -> str:
    title = f"{day} {MONTHS[month - 1]}"
    r = httpx.get(
        "https://ru.wikipedia.org/w/api.php",
        params={
            "action": "query", "prop": "extracts", "explaintext": 1,
            "titles": title, "format": "json", "redirects": 1,
        },
        headers={"User-Agent": "HolidayBot/1.0"},
        timeout=20,
    )
    page = next(iter(r.json()["query"]["pages"].values()))
    text = page.get("extract", "")
    m = re.search(
        r"==\s*Праздники и памятные дни\s*==(.*?)(?:\n==\s*[^=\s]|\Z)",
        text, re.S,
    )
    if not m:
        return f"Не нашёл праздников на {title}."
    body = re.sub(r"=+\s*(.*?)\s*=+", r"\n\1:", m.group(1))
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return f"🎉 Праздники — {title}\n\n{body}"[:4000]


def main():
    now = dt.datetime.now(TZ)
    # В расписании два запуска (лето/зима). Отправляем только в 9 утра по Берлину.
    # При ручном запуске (FORCE=1) отправляем сразу.
    if os.environ.get("FORCE") != "1" and now.hour != 9:
        print(f"Сейчас {now:%H:%M} по Берлину, пропускаю.")
        sys.exit(0)

    text = fetch_holidays(now.day, now.month)
    r = httpx.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )
    r.raise_for_status()
    print("Отправлено.")


if __name__ == "__main__":
    main()
