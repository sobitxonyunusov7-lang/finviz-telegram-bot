from playwright.sync_api import sync_playwright

URL = "https://www.webull.com/quote/nasdaq-cpop"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    )

    page.goto(URL, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # "Analysis" bo'limini bosishga harakat qilamiz
    try:
        page.click("text=Analysis", timeout=10000)
        print("Analysis tab bosildi")
        page.wait_for_timeout(4000)
    except Exception as e:
        print(f"Analysis tab bosilmadi: {e}")

    html = page.content()
    with open("webull_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved webull_page.html")

    # "Cost" yoki "PCD" so'zi borligini tekshiramiz
    if "Cost Distribution" in html or "cost distribution" in html.lower():
        print("MATOPILDI: 'Cost Distribution' matni HTML ichida bor!")
    else:
        print("Cost Distribution matni HTML ichida topilmadi (login kerak bo'lishi yoki JS orqali boshqa joyda yuklanishi mumkin)")

    browser.close()
