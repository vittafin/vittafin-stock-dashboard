# app.py
from flask import Flask, render_template, request
import os
import json

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "news.json")
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

def query_news(stock_filter=None, limit=200):
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    # optional filter by stock or keyword in title
    if stock_filter:
        q = stock_filter.lower()
        data = [d for d in data if q in d.get("stock", "").lower() or q in d.get("title", "").lower()]
    # sort by fetched_at (ISO format)
    data = sorted(data, key=lambda x: x.get("fetched_at", ""), reverse=True)
    return data[:limit]

@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "").strip()
    rows = query_news(stock_filter=q if q else None)
    # distinct stock list for tag buttons
    all_rows = query_news(limit=2000)
    stocks = sorted(list({r.get("stock","").upper() for r in all_rows if r.get("stock")}))
    return render_template("dashboard.html", rows=rows, q=q, stocks=stocks)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
