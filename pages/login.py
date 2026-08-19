import streamlit as st
from config import *
import requests
import time
from streamlit_cookies_controller import CookieController
controller = CookieController()

username = st.text_input(label="Username")
password = st.text_input(label="Password")
if st.button(label="Sign in"):
	st.info("response started")
	response = requests.post(url=f"{API_URL}/login",
	                         data={"username": username, "password": password})
	st.info("response passed")
	if response.status_code == 401:
		st.error("Wrong credentials!")
	elif response.status_code == 200:
		controller.set("access_token", response.json().get("access_token"))
		st.success("Logged in successfully!")
		time.sleep(0.5)  # Cookies don't work without this thing
		st.rerun()
	else:
		st.error(f"Something went wrong: {response.content}")