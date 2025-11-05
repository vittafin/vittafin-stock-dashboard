import requests
import pandas as pd
import sqlite3
from bs4 import BeautifulSoup
import nltk
from datetime import datetime

# Ensure required NLTK data is downloaded
nltk.download("punkt", quiet=True)

# Database setup
DB_PATH = "data/news.db"

def fetch_stock_news():
    """
    Fetches stock market news headlines from a sample website.
    You can later replace this with a real financial news API.
    """
    print("🔍 Fetching latest stock news...")
    
    url = "https://www.moneycontrol.com/news/business/markets/"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch news. Status code: {response.status_code}")
        return pd.DataFrame()
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("li.clearfix")[:10]
    
    titles, summaries, times = [], [], []
    
    for art in articles:
        title_tag = art.select_one("h2 a")
        summary_tag = art.select_one("p")
        
        if title_tag:
            titles.append(title_tag.get_text(strip=True))
            summaries.append(summary_tag.get_text(strip=True) if summary_tag else "No summary available")
            times.append(datetime.now())
    
    df = pd.DataFrame({
        "title": titles,
        "summary": summaries,
        "fetched_at": times
    })
    return df


def save_to_database(df):
    """Save news data to SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            title TEXT,
            summary TEXT,
            fetched_at TIMESTAMP
        )
    """)
    conn.commit()

    # If data found, save it. Else add test data.
    if not df.empty:
        df.to_sql("news", conn, if_exists="replace", index=False)
        print(f"✅ Done! Total {len(df)} news items saved in {DB_PATH}")
    else:
        print("⚠️ No news found. Adding test data...")
        test_data = [
            {"title": "Market Test Update", "summary": "Testing DB save on Render", "fetched_at": pd.Timestamp.now()}
        ]
        pd.DataFrame(test_data).to_sql("news", conn, if_exists="replace", index=False)
        print("✅ Test data added successfully.")

    conn.close()


if __name__ == "__main__":
    df = fetch_stock_news()
    save_to_database(df)
