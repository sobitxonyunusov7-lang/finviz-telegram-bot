import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://finviz.com/screener.ashx?v=111&f=sh_float_u50,sh_price_u1,sh_short_u10,ta_highlow52w_a0to10h,ta_volatility_mo7&ft=4&o=-volume"

SEEN_FILE = "seen.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(data), f, indent=2)


def get_tickers():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        )
        page.goto(URL, timeout=60000, wait_until="networkidle")

        # Jadval elementi paydo bo'lishini kutamiz (JS orqali yuklanadi)
        try:
            page.wait_for_selector("a.screener-link-primary", timeout=15000)
        except Exception:
            print("Jadval kutilgan vaqtda topilmadi, mavjud HTML bilan davom etamiz")

        html = page.content()
        browser.close()

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved page.html")

    soup = BeautifulSoup(html, "html.parser")

    tickers = []
    for a in soup.find_all("a", class_="screener-link-primary"):
        ticker = a.text.strip()
        if ticker and ticker not in tickers:
            tickers.append(ticker)

    print(f"{len(tickers)} ta ticker topildi: {tickers}")
    return tickers


def send_message(text):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(
        api,
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=30
    )
    print("Telegram javobi:", resp.status_code, resp.text[:300])


def main():
    seen = load_seen()
    current = set(get_tickers())

    new = current - seen

    msg = "📊 Finviz New Low\n\n"

    if new:
        msg += "🟢 Yangi New Low:\n"
        for ticker in sorted(new):
            msg += f"🟢 #{ticker}\n"
        msg += "\n"

    msg += "⚪ Barcha New Low:\n"
    for ticker in sorted(current):
        if ticker in new:
            msg += f"🟢 #{ticker}\n"
        else:
            msg += f"⚪ #{ticker}\n"

    msg += f"\n📈 Jami: {len(current)} ta"

    send_message(msg)
    save_seen(current)


if __name__ == "__main__":
    main()
