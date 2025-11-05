# app.py
from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

# Use an absolute path so it works on Render and locally
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "news.db")

# Ensure data folder exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def ensure_db_and_table():
    """Create database file and the news table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create the table if it doesn't exist (columns that your fetch script provides)
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
    conn.commit()
    conn.close()

# Ensure DB/table exists at app startup
ensure_db_and_table()

def query_news(stock_filter=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if stock_filter:
        c.execute("""
            SELECT * FROM news
            WHERE stock LIKE ?
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (f"%{stock_filter}%", limit))
    else:
        c.execute("""
            SELECT * FROM news
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (limit,))
    
    rows = c.fetchall()
    conn.close()
    return rows

@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "").strip()
    rows = query_news(stock_filter=q if q else None)
    # get distinct stock names for quick filter links
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = lambda cursor, row: row[0]
    c = conn.cursor()
    c.execute("SELECT DISTINCT stock FROM news ORDER BY stock ASC")
    stocks = c.fetchall()
    conn.close()
    return render_template("dashboard.html", rows=rows, q=q, stocks=stocks)

if __name__ == "__main__":
    # Local dev: helpful message
    print("Starting Flask app. DB path:", DB_PATH)
    app.run(debug=True, host="0.0.0.0", port=5000)
