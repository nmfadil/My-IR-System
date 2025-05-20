import wikipedia
import re
import io
import requests
from googleapiclient.discovery import build
from gtts import gTTS
from PIL import Image
import speech_recognition as sr
import streamlit as st
from .utils import clean_query

API_KEY = st.secrets["CS_API_KEY"]
CSE_ID = st.secrets["CSE_ID"]

def fetch_answer(query):
    try:
        query = clean_query(query)
        search_results = wikipedia.search(query)
        if not search_results:
            return "Sorry, no results found."
        return wikipedia.summary(search_results[0], sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Too broad. Try one of these: {e.options[:3]}"
    except wikipedia.exceptions.PageError:
        return "Couldn't find a valid Wikipedia page."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def fetch_images(query):
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=CSE_ID, num=5).execute()
        return [
            item.get('pagemap', {}).get('cse_image', [{}])[0].get('src')
            for item in res.get("items", []) if item.get('pagemap', {}).get('cse_image')
        ]
    except Exception:
        return []

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 Listening... please speak now.")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            return "⏱️ Listening timed out. Please try again."
        except sr.UnknownValueError:
            return "😕 Sorry, I couldn't understand your speech."
        except sr.RequestError:
            return "❌ Speech service is unreachable."
