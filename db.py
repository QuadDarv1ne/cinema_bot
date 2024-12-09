import sqlite3
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

DB_PATH = os.getenv("DB_PATH")

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS search_history (
            user_id INTEGER,
            search_query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            search_count INTEGER DEFAULT 0
        )''')
        self.conn.commit()

    def save_search_history(self, user_id, query):
        self.cursor.execute('''INSERT INTO search_history (user_id, search_query) 
                               VALUES (?, ?)''', (user_id, query))
        self.cursor.execute('''INSERT INTO user_stats (user_id, search_count) 
                               VALUES (?, 1) ON CONFLICT(user_id) 
                               DO UPDATE SET search_count = search_count + 1''', (user_id,))
        self.conn.commit()

    def get_search_history(self, user_id):
        self.cursor.execute('''SELECT search_query FROM search_history 
                               WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10''', (user_id,))
        return [row[0] for row in self.cursor.fetchall()]

    def get_user_stats(self, user_id):
        self.cursor.execute('''SELECT search_count FROM user_stats WHERE user_id = ?''', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def close(self):
        self.conn.close()
