# GodBot core memory module
import sqlite3

class MemoryDB:
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename, check_same_thread=False)
        self.create()
    
    def create(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()
    
    def save(self, user_id, role, content):
        self.conn.execute(
            "INSERT INTO memory (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        self.conn.commit()
    
    def get_recent(self, user_id, limit=10):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT role, content FROM memory WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return cur.fetchall()[::-1]

