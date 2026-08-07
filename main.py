from typing import Any, Optional
from datetime import datetime
from fastapi import FastAPI, Path
from pydantic import BaseModel
import sqlite3
from config import *

app = FastAPI()


with sqlite3.connect(NOTES_DB_NAME) as connection:
    cursor = connection.cursor()
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        content TEXT
    );
    """)

"""
get - get information
post - create smth new
put - update
delete - delete smth
"""

class BaseNote(BaseModel):
    name: str
    content: str
    date_posted: datetime

@app.get("/")
async def read_notes():
    with sqlite3.connect(NOTES_DB_NAME) as connection:
        cursor = connection.cursor()
        notes = cursor.execute(
        """
        SELECT * FROM notes;
        """).fetchall()
        return notes

@app.post("/")
async def post_note(note: BaseNote):
    with sqlite3.connect(NOTES_DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
        """
        INSERT INTO notes (name, date_posted, content)
        VALUES (?, ?, ?)
        """,
        (note.name, datetime.now().isoformat(), note.content)
        )

        new_id = cursor.lastrowid
        return {"Success, note id": new_id}
    return {"Fail": ""}