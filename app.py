import streamlit as st
import requests
from config import *

st.set_page_config(page_title="Notes App", layout="wide")
st.title("Notes Dashboard")

# Create two tabs for viewing and adding notes
tab_view, tab_add = st.tabs(["View & Manage Notes", "Add New Note"])

# --- TAB 1: VIEW & DELETE NOTES ---
with tab_view:
	st.header("All Notes")

	if st.button("Refresh Notes"):
		st.rerun()

	try:
		response = requests.get(f"{API_URL}/")
		if response.status_code == 200:
			notes = response.json()

			if not notes:
				st.info("No notes found. Create one in the next tab!")
			else:
				for note in notes:
					note_id, name, date_posted, content = note

					with st.expander(f"{name}"):
						st.caption(f"Posted on: {date_posted}, ID: {note_id}")
						st.write(content)

						if st.button(f"Delete note {note_id}"):
							del_response = requests.delete(f"{API_URL}/{note_id}")
							if del_response.status_code == 200:
								st.success(f"Note {note_id} deleted successfully")
								st.rerun()
							else:
								st.error("Failed to delete the note")
		else:
			st.error(f"Error fetching notes: {response.status_code}")

	except requests.exceptions.ConnectionError:
		st.error("Could not connect to FastAPI backend. Make sure your `main.py` is running on http://127.0.0.1:8000.")

# --- TAB 2: CREATE A NEW NOTE ---
with tab_add:
	st.header("Create a New Note")

	if "success_message" in st.session_state:
		st.success(st.session_state["success_message"])
	if "clear_note_form" not in st.session_state:
		st.session_state["clear_note_form"] = False
	if "note_title" not in st.session_state:
		st.session_state["note_title"] = ""
	if "note_content" not in st.session_state:
		st.session_state["note_content"] = ""

	if st.session_state["clear_note_form"]:
		st.session_state["clear_note_form"] = False
		st.session_state["note_title"] = ""
		st.session_state["note_content"] = ""

	with st.form("create_note_form", clear_on_submit=False):
		name = st.text_input("Note Title", key="note_title")
		content = st.text_area("Note Content", key="note_content")
		submitted = st.form_submit_button("Post Note")

		if submitted:
			if not name.strip() or not content.strip():
				st.warning("Please provide both a title and content.")
			else:
				payload = {"name": name, "content": content}
				try:
					res = requests.post(f"{API_URL}/", json=payload)
					if res.status_code == 200 and res.json().get("status") == "Success":
						st.session_state["clear_note_form"] = True
						st.session_state["success_message"] = (f"Note created successfully! ID: "
						                                       f"{res.json().get('note id')}")
						st.rerun()
					else:
						st.error("Failed to create note.")
				except requests.exceptions.ConnectionError:
					st.error("Backend server is unreachable.")
