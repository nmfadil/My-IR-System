import streamlit as st
from ui import login_page, ir_interface

st.set_page_config(page_title="Information Retrieval System")

# Session and menu control
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"] if not st.session_state["logged_in"] else ["Home"])

if not st.session_state["logged_in"]:
    if menu == "Login":
        login_page.display_login_page()
    else:
        login_page.display_signup_page()
else:
    ir_interface.run_interface()
