"""Надсилає свята та незвичайні дні за сьогодні в Telegram (українською)."""
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

MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня",
          "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]

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
        r = httpx.get("https://uk.wikipedia.org/w/api.php",
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
        raise RuntimeError(f"Вікіпедія не відповіла: {last}")

    page = next(iter(data["query"]["pages"].values()))
    text = page.get("extract", "")

    # розділ "Свята та пам'ятні дні" (назва може трохи відрізнятись)
    m = re.search(
        r"\n==\s*Свята[^=\n]*==(.*?)(?=\n==\s*[^=\s]|\Z)",
        text, re.S,
    )
    if not m:
        return f"Не знайшов свят на {title}."

    body = m.group(1)
    body = re.sub(r"=+\s*(.*?)\s*=+", r"\n\1:", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    msg = f"🎉 Свята та незвичайні дні — {title}\n\n{body}"
    if len(msg) > 4000:
        msg = msg[:4000].rsplit("\n", 1)[0] + "\n…"
    return msg


def main():
    now = dt.datetime.now(TZ)
    if os.environ.get("FORCE") != "1" and now.hour != 9:
        print(f"Зараз {now:%H:%M} за Берліном, пропускаю.")
        sys.exit(0)

    text = fetch_holidays(now.day, now.month)
    r = httpx.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )
    if r.status_code != 200:
        print("Telegram відповів:", r.status_code, r.text)
    r.raise_for_status()
    print("Надіслано.")


if __name__ == "__main__":
    main()
