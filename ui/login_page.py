import streamlit as st
from modules.auth import authenticate_user, add_user

def display_signup_page():
    st.title("Sign Up")
    new_name = st.text_input("Full Name")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")

    if st.button("Sign Up"):
        if new_username and new_password and new_name:
            from modules.auth import supabase  # for checking existing
            existing = supabase.table("users").select("id").eq("username", new_username).execute()
            if existing.data:
                st.error("Username already exists.")
            else:
                res = add_user(new_username, new_name, new_password)
                if res.data:
                    st.success("Account created! You can now log in.")
                else:
                    st.error("Signup failed.")
        else:
            st.warning("Please fill all fields.")

def display_login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        name = authenticate_user(username, password)
        if name:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["user_fullname"] = name
            st.success(f"Welcome, {name}!")
            st.rerun()
        else:
            st.error("Incorrect credentials.")
