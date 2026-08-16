from typing import Any, Optional
from datetime import datetime
from argon2 import PasswordHasher
import secret
import argon2.exceptions
from fastapi import FastAPI, Path, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import sqlite3
import jwt
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


class BaseNote(BaseModel):
	name: str
	content: str


# date_posted: datetime


class UserRegister(BaseModel):
	username: str
	password: str


class UserLogin(BaseModel):
	username: str
	password: str


# though it looks just like UserRegister now, I'm going to leave two classes instead of one
# because probably they will be different in future

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user_id(token: str = Depends(oauth2_scheme)):
	try:
		payload = jwt.decode(token, secret.SECRET_KEY, algorithms=["HS256"])
		user_id = payload.get("id")

		if user_id is None:
			raise HTTPException(status_code=401, detail="Wrong token")
		return user_id
	except jwt.exceptions.DecodeError:
		raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/")
def get_all_notes(user_id: int = Depends(get_current_user_id)):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		notes = cursor.execute(
			"""
			SELECT * FROM notes WHERE user_id = ?;
			""", (user_id,)).fetchall()
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
			return {"Success": f"User registered successfully"}
		except sqlite3.IntegrityError:
			raise HTTPException(status_code=400, detail="User with such username already exists")


@app.post("/login")
def login(user: UserLogin):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()

		result = cursor.execute(
			"""
			SELECT id, password_hash FROM users WHERE username = ?
			""", (user.username,)
		).fetchone()

		if result is None:
			raise HTTPException(status_code=400, detail="User with such username doesn't exist")
		password_hash_from_db = result[1]
		user_id = result[0]

		hasher = PasswordHasher()
		try:
			hasher.verify(password_hash_from_db, user.password)
		except argon2.exceptions.VerifyMismatchError:
			raise HTTPException(status_code=400, detail="Wrong password!")

		payload = {"username": user.username, "id": user_id}
		token = jwt.encode(payload, secret.SECRET_KEY, algorithm="HS256")
		return {"access_token": token, "token_type": "bearer"}


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
