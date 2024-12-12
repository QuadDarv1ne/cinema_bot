import sqlite3
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from datetime import datetime

# Загружаем переменные окружения из .env файла
load_dotenv()

DB_PATH = os.getenv("DB_PATH")

class Database:
    def __init__(self):
        self.create_tables()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        try:
            yield conn
        finally:
            conn.close()

    def create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS search_history (
                user_id INTEGER,
                search_query TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                search_count INTEGER DEFAULT 0
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS movie_details (
                search_query TEXT PRIMARY KEY,
                movie_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.commit()

    def save_search_history(self, user_id, query):
        timestamp = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO search_history (user_id, search_query, timestamp) 
                               VALUES (?, ?, ?)''', (user_id, query, timestamp))
            cursor.execute('''INSERT INTO user_stats (user_id, search_count) 
                               VALUES (?, 1) 
                               ON CONFLICT(user_id) 
                               DO UPDATE SET search_count = search_count + 1''', (user_id,))
            conn.commit()

    def save_movie_details(self, query, movie_data):
        timestamp = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO movie_details (search_query, movie_data, timestamp) 
                               VALUES (?, ?, ?) 
                               ON CONFLICT(search_query) 
                               DO UPDATE SET movie_data = ?, timestamp = ?''',
                           (query, movie_data, timestamp, movie_data, timestamp))
            conn.commit()

    def get_movie_details(self, query):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT movie_data FROM movie_details WHERE search_query = ?''', (query,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_search_history(self, user_id, limit=10):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT search_query FROM search_history 
                               WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?''', (user_id, limit))
            return [row[0] for row in cursor.fetchall()]

    def get_user_stats(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT search_count FROM user_stats WHERE user_id = ?''', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_top_searches(self, limit=10):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT search_query, COUNT(*) as frequency 
                               FROM search_history 
                               GROUP BY search_query 
                               ORDER BY frequency DESC 
                               LIMIT ?''', (limit,))
            return cursor.fetchall()
