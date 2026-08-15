from typing import Any, Optional
from datetime import datetime
from fastapi import FastAPI, Path, HTTPException
from pydantic import BaseModel
import sqlite3
from argon2 import PasswordHasher
from config import *

app = FastAPI()

with sqlite3.connect(DB_NAME) as connection:
	cursor = connection.cursor()
	cursor.execute(
		"""
		CREATE TABLE IF NOT EXISTS notes (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			date_posted DATE,
			content TEXT,
			user_id INTEGER,
			FOREIGN KEY (user_id) REFERENCES users (id)
		);
		""")
with sqlite3.connect(DB_NAME) as connection:
	cursor = connection.cursor()
	cursor.execute(
		"""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT UNIQUE,
			password_hash TEXT
		);
		"""
	)

"""
get - get information
post - create smth new
put - update
delete - delete smth
"""


class BaseNote(BaseModel):
	name: str
	content: str
	user_id: int


# date_posted: datetime


class UserRegister(BaseModel):
	username: str
	password: str


@app.get("/")
def get_all_notes():
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		notes = cursor.execute(
			"""
			SELECT * FROM notes;
			""").fetchall()
		return notes


@app.post("/")
def post_note(note: BaseNote):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		try:
			cursor.execute(
				"""
				INSERT INTO notes (name, date_posted, content)
				VALUES (?, ?, ?, ?)
				""", (note.name, datetime.now().isoformat(), note.content, note.user_id)
			)
			new_id = cursor.lastrowid
			return {"status": "Success", "note id": new_id}
		except:
			raise HTTPException(status_code=400, detail="Failed to post note")


@app.post("/register")
def register(user: UserRegister):
	if len(user.password) < MIN_PASSWORD_LENGTH:
		raise HTTPException(status_code=400, detail=f"Password length must be at least "
		                                            f"{MIN_PASSWORD_LENGTH} characters long")
	if len(user.username) < MIN_USERNAME_LENGTH:
		raise HTTPException(status_code=400, detail=f"Username length must be at least "
		                                            f"{MIN_USERNAME_LENGTH} characters long")
	hasher = PasswordHasher()
	password_hashed = hasher.hash(user.password)

	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		try:
			cursor.execute(
				"""
				INSERT INTO users (username, password_hash)
				VALUES (?, ?)
				""", (user.username, password_hashed)
			)
			return {"Success": "User registered successfully"}
		except sqlite3.IntegrityError:
			raise HTTPException(status_code=400, detail="User with such username already exists")


@app.get("/{note_id}")
def get_note_by_id(note_id: int):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		note = cursor.execute("""
            SELECT * FROM notes WHERE id = ?
        """, (note_id,)).fetchall()
		if len(note) == 0:
			raise HTTPException(status_code=400, detail="Note with this id doesn't exist")
		else:
			return note


@app.delete("/{note_id}")
def delete_note_by_id(note_id: int):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		cursor.execute("""
            DELETE FROM notes WHERE id = ?
        """, (note_id,))
		if cursor.rowcount > 0:
			return {"status": f"Successfully deleted note with id {note_id}"}
		else:
			raise HTTPException(status_code=400, detail=f"Couldn't delete note with id {note_id}")
