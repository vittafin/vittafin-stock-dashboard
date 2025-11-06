# fetch_news.py
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

# --- Configuration ---
# Put the stock symbols you want to track here (upper-case).
# You can replace this small list with your full holdings list when ready.
stocks = [
    "RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK"
]

# Output file (same "data" folder used by the app)
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "news.json")

# Ensure folder exists
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_stock_news(stock):
    """Scrape Moneycontrol tag page for a stock and return list of dicts."""
    url = f"https://www.moneycontrol.com/news/tags/{stock.lower()}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=12)
    except Exception as e:
        print(f"⚠️ Request failed for {stock}: {e}")
        return []

    if r.status_code != 200:
        print(f"⚠️ Non-200 for {stock}: {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("li.clearfix")  # Moneycontrol pattern used earlier
    results = []
    for it in items[:12]:  # limit per stock to avoid huge fetch
        title_tag = it.select_one("h2 a")
        summary_tag = it.select_one("p")
        date_tag = it.select_one(".dateline")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag.get("href")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        published = date_tag.get_text(strip=True) if date_tag else ""
        results.append({
            "stock": stock,
            "title": title,
            "link": link,
            "narration": summary,
            "published": published,
            "fetched_at": datetime.utcnow().isoformat()
        })
    return results

def main():
    all_news = []
    seen_links = set()
    print("🔍 Fetching latest stock news...")
    for s in stocks:
        try:
            items = fetch_stock_news(s)
        except Exception as e:
            items = []
            print(f"⚠️ Error fetching {s}: {e}")
        # dedupe by link
        for it in items:
            if it["link"] and it["link"] not in seen_links:
                seen_links.add(it["link"])
                all_news.append(it)
        sleep(1)  # small pause between requests

    # Save
    if all_news:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_news, f, ensure_ascii=False, indent=2)
        print(f"✅ Done! Total {len(all_news)} news items saved in {DATA_FILE}")
    else:
        # fallback test record so you can confirm dashboard pipeline
        test = [{
            "stock": "TEST",
            "title": "Market Test Update",
            "link": "#",
            "narration": "Testing JSON save on Render",
            "published": "",
            "fetched_at": datetime.utcnow().isoformat()
        }]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(test, f, ensure_ascii=False, indent=2)
        print("⚠️ No news found. Test data added successfully.")

if __name__ == "__main__":
    main()
