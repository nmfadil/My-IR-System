import hashlib
from supabase import create_client
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DEBUG = True

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, name, password):
    if not DEBUG:
        password = hash_password(password)
    return supabase.table("users").insert({
        "username": username,
        "name": name,
        "password": password
    }).execute()

def authenticate_user(username, password):
    if not DEBUG:
        password = hash_password(password)
    res = supabase.table("users").select("name").eq("username", username).eq("password", password).execute()
    return res.data[0]["name"] if res.data else None
