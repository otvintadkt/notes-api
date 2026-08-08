from typing import Any, Optional
from datetime import datetime
from fastapi import FastAPI, Path
from fastapi.responses import HTMLResponse
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
			date_posted DATE,
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
	# date_posted: datetime


@app.get("/")
def get_all_notes():
	with sqlite3.connect(NOTES_DB_NAME) as connection:
		cursor = connection.cursor()
		notes = cursor.execute(
			"""
			SELECT * FROM notes;
			""").fetchall()
		return notes


@app.post("/")
def post_note(note: BaseNote):
	with sqlite3.connect(NOTES_DB_NAME) as connection:
		cursor = connection.cursor()
		try:
			cursor.execute("""
            INSERT INTO notes (name, date_posted, content)
            VALUES (?, ?, ?)
            """,
			               (note.name, datetime.now().isoformat(), note.content)
			               )
			new_id = cursor.lastrowid
			return {"Success, note id": new_id}
		except:
			return {"Fail"}


@app.get("/{note_id}")
def get_note_by_id(note_id: int):
	with sqlite3.connect(NOTES_DB_NAME) as connection:
		cursor = connection.cursor()
		note = cursor.execute("""
            SELECT * FROM notes WHERE id = ?
        """, (note_id,)).fetchall()
		if len(note) == 0:
			return {"Note with this id doesn't exist"}
		else:
			return note


def delete_note_by_id(note_id: int):
	with sqlite3.connect(NOTES_DB_NAME) as connection:
		cursor = connection.cursor()
		cursor.execute("""
            DELETE FROM notes WHERE id = ?
        """, (note_id,))
		if cursor.rowcount > 0:
			return {f"Successfully deleted note with id {note_id}"}
		else:
			return {f"Couldn't delete note with id {note_id}"}
