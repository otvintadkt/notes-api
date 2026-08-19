import streamlit as st
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="Notes App", layout="wide")
st.title("Notes Dashboard")
controller = CookieController()

login_page = st.Page("pages/login.py", url_path="/login")
dashboard_page = st.Page("pages/main_page.py")
post_note_page = st.Page("pages/post_note.py")
register_page = st.Page("pages/register.py")
pg = st.navigation([login_page, dashboard_page, post_note_page, register_page])
pg.run()
