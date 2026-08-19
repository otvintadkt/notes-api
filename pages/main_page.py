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
response = requests.get(url=f"{API_URL}/", headers=headers)
st.write(response.json())
