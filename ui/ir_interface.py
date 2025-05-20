import streamlit as st
from PIL import Image
import io
import requests
from modules.ir_core import fetch_answer, fetch_images, text_to_speech, speech_to_text
from modules.utils import clean_query

def run_interface():
    st.title("Information Retrieval System")
    st.write(f"Welcome, {st.session_state.get('user_fullname', 'User')}")

    if "img_index" not in st.session_state:
        st.session_state.img_index = 0
    if "img_urls" not in st.session_state:
        st.session_state.img_urls = []

    input_method = st.radio("Choose input method:", ("Text", "Speech"))
    query = ""

    if input_method == "Text":
        query = st.text_input("Enter your query (e.g., 'Albert Einstein')")
    else:
        if st.button("🎙️ Record Speech"):
            result = speech_to_text()
            if not result.startswith(("⏱️", "😕", "❌")):
                query = result
                st.write("🗣️ You said:", result)
            else:
                st.warning(result)

    if query and st.button("Get Answer"):
        with st.spinner("Fetching answer..."):
            query = clean_query(query)
            answer = fetch_answer(query)
            audio = text_to_speech(answer)
            st.audio(audio, format='audio/mp3')

            st.session_state.answer = answer
            st.session_state.img_urls = fetch_images(query)
            st.session_state.img_index = 0

    if "answer" in st.session_state:
        st.subheader("Answer:")
        st.write(st.session_state.answer)

    if st.session_state.img_urls:
        img_url = st.session_state.img_urls[st.session_state.img_index]
        try:
            response = requests.get(img_url, timeout=5)
            img = Image.open(io.BytesIO(response.content))
            st.image(img, caption=f"Image {st.session_state.img_index + 1}")
        except Exception:
            st.warning("Could not load image.")

        if st.button("➡️ Next Image"):
            st.session_state.img_index = (st.session_state.img_index + 1) % len(st.session_state.img_urls)

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
