import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Har bir screener: nomi, URL manzili, va "seen" ro'yxati saqlanadigan fayl
SCREENERS = [
    {
        "name": "New Low",
        "url": "https://finviz.com/screener?v=111&s=ta_newlow&f=sh_float_u50,sh_price_u1,sh_short_u10,ta_volatility_mo7&ft=4&o=-volume",
        "seen_file": "seen_new_low.json",
    },
    {
        "name": "52 High/Low",
        "url": "https://finviz.com/screener?v=111&f=sh_float_u50,sh_price_u1,sh_short_u10,ta_highlow52w_a0to10h,ta_volatility_mo7&ft=4&o=-volume",
        "seen_file": "seen_52_high_low.json",
    },
]


def load_seen(seen_file):
    if os.path.exists(seen_file):
        with open(seen_file, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_file, data):
    with open(seen_file, "w") as f:
        json.dump(list(data), f, indent=2)


def get_tickers(url, page_html_path):
    all_tickers = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        )

        row_offset = 1
        page_size = 20
        full_html = ""

        while True:
            page_url = url if row_offset == 1 else f"{url}&r={row_offset}"
            page.goto(page_url, timeout=60000, wait_until="domcontentloaded")

            try:
                page.wait_for_selector("table.screener_table", timeout=30000)
            except Exception:
                print(f"r={row_offset}: jadval kutilgan vaqtda topilmadi")

            html = page.content()
            if row_offset == 1:
                full_html = html

            soup = BeautifulSoup(html, "html.parser")
            page_tickers = []
            for td in soup.find_all(attrs={"data-boxover-ticker": True}):
                ticker = td["data-boxover-ticker"].strip()
                if ticker and ticker not in page_tickers:
                    page_tickers.append(ticker)

            if not page_tickers:
                break

            new_on_page = [t for t in page_tickers if t not in all_tickers]
            all_tickers.extend(new_on_page)

            print(f"r={row_offset}: {len(page_tickers)} ta topildi (jami hozircha: {len(all_tickers)})")

            if len(page_tickers) < page_size or not new_on_page:
                break

            row_offset += page_size

        browser.close()

    with open(page_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Jami {len(all_tickers)} ta ticker topildi: {all_tickers}")
    return all_tickers


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


def process_screener(screener):
    name = screener["name"]
    url = screener["url"]
    seen_file = screener["seen_file"]
    page_html_path = f"page_{seen_file.replace('.json', '')}.html"

    print(f"\n=== {name} ekranini tekshirish ===")

    seen = load_seen(seen_file)
    current = set(get_tickers(url, page_html_path))

    new = current - seen

    if not new:
        print(f"{name}: yangi ticker yo'q, xabar yuborilmadi.")
        save_seen(seen_file, current)
        return

    msg = f"📊 Finviz {name} — yangi belgilar aniqlandi!\n\n"
    msg += "🟢 Yangi:\n"
    for ticker in sorted(new):
        msg += f"🟢 #{ticker}\n"

    msg += "\n⚪ Barchasi:\n"
    for ticker in sorted(current):
        if ticker in new:
            msg += f"🟢 #{ticker}\n"
        else:
            msg += f"⚪ #{ticker}\n"

    msg += f"\n📈 Jami: {len(current)} ta"

    send_message(msg)
    save_seen(seen_file, current)


def main():
    for screener in SCREENERS:
        process_screener(screener)


if __name__ == "__main__":
    main()
