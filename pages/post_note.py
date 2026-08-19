import streamlit as st
from streamlit_cookies_controller import CookieController
import requests
from config import *

controller = CookieController()


def get_headers():
	if controller.get("access_token"):
		return {"Authorization": f"Bearer {controller.get("access_token")}"}
	else:
		return {}


headers = get_headers()
title = st.text_input("Note title")
content = st.text_area("Note content")

if st.button("Post note"):
	payload = {"name": title, "content": content}
	response = requests.post(url=f"{API_URL}/post_note", headers=headers, json=payload)
	st.info(response.status_code)
	if response.status_code == 200:
		st.success("Posted!")
	st.rerun()
