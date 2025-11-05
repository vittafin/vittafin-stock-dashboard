import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import nltk

# Ensure nltk dependencies exist
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# === Setup paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'news.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# === Connect DB and create table if not exists ===
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock TEXT,
    title TEXT,
    link TEXT,
    published TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# === Your stock list (you can add all your holdings here) ===
stocks = ["RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK"]

# === Fetch news from Moneycontrol (example pattern) ===
def fetch_stock_news(stock):
    url = f"https://www.moneycontrol.com/news/tags/{stock.lower()}.html"
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    news_items = []

    for item in soup.select("li.clearfix"):
        title_tag = item.select_one("h2 a")
        date_tag = item.select_one(".dateline")
        if title_tag:
            title = title_tag.text.strip()
            link = title_tag.get("href")
            published = date_tag.text.strip() if date_tag else ""
            news_items.append((stock, title, link, published))
    return news_items

# === Save news to DB ===
def save_news(news_list):
    c.executemany('INSERT INTO news (stock, title, link, published) VALUES (?, ?, ?, ?)', news_list)
    conn.commit()

total_saved = 0
for s in stocks:
    news_data = fetch_stock_news(s)
    save_news(news_data)
    total_saved += len(news_data)

conn.close()
print(f"✅ Done! Total {total_saved} news items saved in {DB_PATH}")
