from datetime import datetime, timedelta
import logging

class Cache:
    def __init__(self, expiration: timedelta = timedelta(minutes=10)):
        self.cache = {}
        self.expiration = expiration

    def has(self, query):
        if query in self.cache:
            timestamp, data = self.cache[query]
            if datetime.now() - timestamp < self.expiration:
                return True
            else:
                del self.cache[query]  # Удаляем устаревшие данные
        return False

    def get(self, query):
        return self.cache[query][1] if self.has(query) else None

    def set(self, query, data):
        self.cache[query] = (datetime.now(), data)

    def clear(self):
        """Очищаем весь кэш"""
        self.cache = {}

    def remove(self, query):
        """Удаляем конкретный элемент из кэша"""
        if query in self.cache:
            del self.cache[query]
