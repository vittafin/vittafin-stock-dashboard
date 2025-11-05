import os
import time
import requests
import pandas as pd
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
import nltk

# --- NLTK setup ---
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    print("Downloading NLTK punkt model...")
    nltk.download("punkt")
from nltk.tokenize import sent_tokenize


# === Your Stock Holdings ===
HOLDINGS = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY"]

# === Custom Slug Mappings ===
CUSTOM_SLUGS = {
    "RELIANCE": "reliance-industries",
    "HDFCBANK": "hdfc-bank",
    "ICICIBANK": "icici-bank",
    "INFY": "infosys",
    "TCS": "tata-consultancy-services",
}

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "news.db")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get_slug(stock_name):
    if stock_name in CUSTOM_SLUGS:
        return CUSTOM_SLUGS[stock_name]
    return stock_name.lower().replace(" ", "-").replace("&", "and").replace(".", "")


def fetch_tag_page(stock_name):
    slug = get_slug(stock_name)
    url = f"https://www.moneycontrol.com/news/tags/{slug}.html"
    print(f"🔗 {stock_name}: Fetching {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"Error fetching tag page for {stock_name}: {e}")
    return None


def parse_links_from_tag(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    links = []

    # New Moneycontrol structure: 'li' with 'clearfix' replaced by 'list_item' or article links inside <a href="">
    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]
        if (
            href.startswith("https://www.moneycontrol.com/news/")
            and len(title) > 25
            and "video" not in href
        ):
            links.append((title, href))

    seen = set()
    unique_links = [(t, l) for t, l in links if not (l in seen or seen.add(l))]

    print(f"   ➜ Found {len(unique_links)} links")
    return unique_links


def fetch_article_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = [p.get_text(strip=True) for p in soup.select("p")]
        full_text = "\n".join(paragraphs[:5])
        return full_text if full_text else None
    except Exception:
        return None


def make_narration(article_text: str, max_sentences=2) -> str:
    try:
        sentences = sent_tokenize(article_text)
        return " ".join(sentences[:max_sentences]).strip()
    except Exception:
        return article_text[:300]


def save_to_db(rows):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT,
            title TEXT,
            link TEXT UNIQUE,
            narration TEXT,
            fetched_at TEXT
        )
    """)
    for r in rows:
        try:
            c.execute("""
                INSERT OR IGNORE INTO news (stock, title, link, narration, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (r['stock'], r['title'], r['link'], r['narration'], r['fetched_at']))
        except Exception as e:
            print("DB insert error:", e)
    conn.commit()
    conn.close()


def process_stock(stock_name: str, limit=3, delay=1.0):
    html = fetch_tag_page(stock_name)
    if not html:
        print(f"⚠️ No tag page for {stock_name}")
        return []

    articles = parse_links_from_tag(html)
    if not articles:
        print(f"⚠️ No news found for {stock_name}")
        return []

    rows = []
    for title, link in articles[:limit]:
        article_text = fetch_article_text(link)
        if not article_text:
            continue
        narration = make_narration(article_text)
        rows.append({
            "stock": stock_name,
            "title": title,
            "link": link,
            "narration": narration,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        time.sleep(delay)
    return rows


def main():
    all_rows = []
    print("🚀 Starting news fetch...")
    for i, stock in enumerate(HOLDINGS, 1):
        print(f"[{i}/{len(HOLDINGS)}] Fetching {stock}...")
        rows = process_stock(stock, limit=3, delay=0.8)
        if rows:
            save_to_db(rows)
            all_rows.extend(rows)
    print(f"\n✅ Done! Total {len(all_rows)} news items saved in {DB_PATH}")


if __name__ == "__main__":
    main()
