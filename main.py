from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from datetime import datetime

app = FastAPI(title="Сервис сбора отзывов")

DB_PATH = "reviews.db"

POSITIVE = [
    "хорош", "отличн", "люблю",
    "супер", "класс", "нравит",
    "прекрасн", "удобн", "быстр",
    "рекоменд"
]
NEGATIVE = [
    "плохо", "ужас", "ненавиж",
    "отстой", "проблем", "глюч",
    "медлен", "неудобн", "разочар",
    "бесит"
]


def get_db():
    """
    Открывает соединение с базой данных SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Инициализирует базу данных и создает таблицу reviews,
    если она не существует.
    """
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


init_db()


def get_sentiment(text: str) -> str:
    """
    Определяет настроение отзыва по ключевым словам.
    Возвращает 'positive', 'negative' или 'neutral'.
    """
    t = text.lower()
    if any(word in t for word in POSITIVE):
        return "positive"
    if any(word in t for word in NEGATIVE):
        return "negative"
    return "neutral"


class ReviewIn(BaseModel):
    """
    Модель входящего отзыва.
    """
    text: str


class ReviewOut(BaseModel):
    """
    Модель исходящего отзыва с определённым настроением.
    """
    id: int
    text: str
    sentiment: str
    created_at: str


@app.post("/reviews", response_model=ReviewOut)
def create_review(review: ReviewIn):
    """
    Принимает отзыв, определяет его настроение,
    сохраняет в БД и возвращает результат.
    """
    sentiment = get_sentiment(review.text)
    created_at = datetime.utcnow().isoformat()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
        (review.text, sentiment, created_at)
    )
    conn.commit()
    review_id = cur.lastrowid
    conn.close()
    return {
        "id": review_id,
        "text": review.text,
        "sentiment": sentiment,
        "created_at": created_at
    }


@app.get("/reviews", response_model=List[ReviewOut])
def list_reviews(
        sentiment: Optional[str] = Query(
            None, description="Filter by sentiment"
        )
):
    """
    Возвращает список отзывов. Можно фильтровать по настроению (sentiment).
    """
    conn = get_db()
    cur = conn.cursor()
    if sentiment:
        cur.execute("SELECT * FROM reviews WHERE sentiment = ?", (sentiment,))
    else:
        cur.execute("SELECT * FROM reviews")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
