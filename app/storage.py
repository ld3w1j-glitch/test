import os, sqlite3, csv
from datetime import datetime
from flask import current_app

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "history.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            count INTEGER NOT NULL,
            corrected_count INTEGER,
            mode TEXT,
            original_file TEXT,
            processed_file TEXT,
            note TEXT
        )
    """)
    con.commit()
    con.close()

def add_history(count, mode, original_file="", processed_file="", note=""):
    init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO history (created_at, count, corrected_count, mode, original_file, processed_file, note)
        VALUES (?, ?, NULL, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(count), mode, original_file, processed_file, note))
    con.commit()
    row_id = cur.lastrowid
    con.close()
    return row_id

def list_history(limit=200):
    init_db()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]

def update_corrected(item_id, corrected_count, note=""):
    init_db()
    con = sqlite3.connect(DB_PATH)
    con.execute("UPDATE history SET corrected_count=?, note=? WHERE id=?", (int(corrected_count), note, int(item_id)))
    con.commit()
    con.close()

def export_csv(path):
    rows = list_history(100000)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id","created_at","count","corrected_count","mode","original_file","processed_file","note"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)