from typing import Annotated
from datetime import datetime
from argon2 import PasswordHasher
import secret
import argon2.exceptions
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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

UserIdDep = Annotated[int, Depends(get_current_user_id)]

@app.get("/")
def get_all_notes(user_id: int = Depends(get_current_user_id)):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		notes = cursor.execute(
			"""
			SELECT * FROM notes WHERE user_id = ?;
			""", (user_id,)
		).fetchall()
		return notes


@app.post("/post_note")
def post_note(note: BaseNote, user_id: UserIdDep):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		try:
			cursor.execute(
				"""
				INSERT INTO notes (name, date_posted, content, user_id)
				VALUES (?, ?, ?, ?)
				""", (note.name, datetime.now().isoformat(), note.content, user_id)
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
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()

		result = cursor.execute(
			"""
			SELECT id, password_hash FROM users WHERE username = ?
			""", (form_data.username,)
		).fetchone()

		if result is None:
			raise HTTPException(status_code=401, detail="User with such username doesn't exist")
		password_hash_from_db = result[1]
		user_id = result[0]

		hasher = PasswordHasher()
		try:
			hasher.verify(password_hash_from_db, form_data.password)
		except argon2.exceptions.VerifyMismatchError:
			raise HTTPException(status_code=401, detail="Wrong password!")

		payload = {"username": form_data.username, "id": user_id}
		token = jwt.encode(payload, secret.SECRET_KEY, algorithm="HS256")
		return {"access_token": token, "token_type": "bearer"}


@app.get("/{note_id}")
def get_note_by_id(note_id: int, user_id: UserIdDep):
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		note = cursor.execute(
			"""
            SELECT id, name, date_posted, content, user_id FROM notes WHERE id = ?
            """, (note_id,)
		).fetchone()

		if note is None:
			raise HTTPException(status_code=404, detail="Note not found")
		note_owner_id = note[4]
		if note_owner_id != user_id:
			raise HTTPException(status_code=403, detail="You do not have access to this note")
		return {
			"id": note[0],
			"name": note[1],
			"date_posted": note[2],
			"content": note[3]
		}


@app.delete("/{note_id}")
def delete_note_by_id(note_id: int, user_id: UserIdDep):
	get_note_by_id(note_id, user_id) # Checking access and existence of such note
	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		cursor.execute(
			"""
            DELETE FROM notes WHERE id = ? AND user_id = ?
            """, (note_id, user_id)
		)
		if cursor.rowcount > 0:
			return {"status": f"Successfully deleted note with id {note_id}"}
		else:
			raise HTTPException(status_code=400, detail=f"Couldn't delete note with id {note_id}")
