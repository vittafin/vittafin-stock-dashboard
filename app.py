from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join("data", "news.db")

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
    if not os.path.exists(DB_PATH):
        print("⚠️  No database found. Please run fetch_news.py first.")
    app.run(debug=True, port=5000)
