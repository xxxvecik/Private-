"""Отправляет праздники за сегодня в Telegram. Запускается из GitHub Actions."""
import datetime as dt
import os
import re
import sys
import time
from zoneinfo import ZoneInfo

import httpx

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TZ = ZoneInfo("Europe/Berlin")

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]

HEADERS = {
    "User-Agent": "HolidayTelegramBot/1.0 "
                  "(https://github.com/xxxvecik/Private-; personal use) httpx"
}


def fetch_holidays(day: int, month: int) -> str:
    title = f"{day} {MONTHS[month - 1]}"
    params = {
        "action": "query", "prop": "extracts", "explaintext": 1,
        "titles": title, "format": "json", "redirects": 1,
    }
    data, last = None, ""
    for _ in range(3):
        r = httpx.get("https://ru.wikipedia.org/w/api.php",
                      params=params, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            try:
                data = r.json()
                break
            except ValueError:
                pass
        last = f"{r.status_code} {r.text[:200]}"
        time.sleep(3)
    if data is None:
        raise RuntimeError(f"Википедия не ответила: {last}")

    page = next(iter(data["query"]["pages"].values()))
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
