import requests
from bs4 import BeautifulSoup
import json
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://finviz.com/screener.ashx?v=111&f=sh_float_u50,sh_price_u1,sh_short_u10,ta_highlow52w_a0to10h,ta_volatility_mo7&ft=4&o=-volume"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SEEN_FILE = "seen.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(data), f)
        
def get_tickers():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "lxml")

    tickers = []

    for a in soup.find_all("a", class_="screener-link-primary"):
        ticker = a.text.strip()
        if ticker:
            tickers.append(ticker)

    return tickers


def send_message(text):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        api,
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=30
    )
    
def main():
    seen = load_seen()
    current = set(get_tickers())

    new = current - seen

    if new:
        msg = "🚨 New Finviz Alert\n\n"
        for ticker in sorted(new):
            msg += f"#{ticker}\n"

        send_message(msg)

    save_seen(current)


if __name__ == "__main__":
    main()
