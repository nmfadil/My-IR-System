#2nd with wiki and pdf
import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from modules.ir_core import speech_to_text,fetch_answer,text_to_speech,fetch_images,get_pdf_text,get_text_chunks,get_vectorstore
from modules.utils import clean_query
import requests
from PIL import Image
import io

groq_api_key = st.secrets["GROQ_API_KEY"]

def render_ir_app():
    st.title("Information Retrieval System")
    st.write(f"Welcome, {st.session_state.get('user_fullname', 'User')}")
    mode = st.selectbox("Choose Retrieval Mode", ["Wikipedia IR", "PDF IR"])

    if mode == "Wikipedia IR":
        render_wikipedia_ir()
    elif mode == "PDF IR":
        render_pdf_ir()
    
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

def render_wikipedia_ir():
    if "img_index" not in st.session_state:
        st.session_state.img_index = 0
    if "img_urls" not in st.session_state:
        st.session_state.img_urls = []

    input_method = st.radio("Choose input method:", ("Text", "Speech"))
    query = ""

    if input_method == "Text":
        query = st.text_input("Enter your query")
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

def render_pdf_ir():
    st.subheader("📄 PDF-Based IR")
        # Initialize model once per session
    if 'model' not in st.session_state:
        st.session_state.model = Groq(
            id="llama-3.1-8b-instant",
            api_key=groq_api_key
        )
        # IR system system prompt and instructions
    system_prompt = """
    You are an intelligent and helpful Information Retrieval assistant. Your job is to find and summarize relevant information precisely and clearly, without unnecessary filler or verbosity. You provide concise, factual answers and highlight the most important parts from documents or queries.
    """

    instructions = """
    1. Focus on answering queries by extracting the most relevant information.
    2. Use clear, straightforward language suitable for users of all backgrounds.
    3. When responding with extracted content, keep it brief and on point.
    4. If the answer is not found, politely state that information is unavailable.
    5. Avoid speculation or providing unrelated content.
    """

    # Initialize agent for IR system (no history or storage)
    if 'ir_agent' not in st.session_state:
        st.session_state.ir_agent = Agent(
            model=st.session_state.model,
            role="Information Retrieval Assistant",
            description=system_prompt,
            instructions=instructions,
            storage=None,  # no history storage
            add_history_to_messages=False
        )

    uploaded_pdf = st.file_uploader("Upload a PDF document", type=["pdf"])

    if uploaded_pdf:
        st.success("✅ PDF uploaded successfully.")
        current_filename = uploaded_pdf.name

        # Auto-reset if a new file is uploaded
        if st.session_state.get("pdf_filename") != current_filename:
            st.session_state.clear()  # Clear everything related to the previous session
            st.session_state["pdf_filename"] = current_filename

        if "vectorstore" not in st.session_state:
            with st.spinner("📄 Extracting, chunking, and embedding..."):
                try:
                    # Step 1: Extract
                    raw_text = get_pdf_text(uploaded_pdf)
                    st.session_state["pdf_text"] = raw_text

                    # Step 2: Chunk
                    chunks = get_text_chunks(raw_text)
                    st.session_state["pdf_chunks"] = chunks

                    # Step 3: Embed & Store
                    vectorstore = get_vectorstore(chunks)
                    st.session_state["vectorstore"] = vectorstore

                    st.success("✅ Vectorstore ready. You can now ask questions from this PDF.")
                    #st.text_area("📖 Preview Extracted Text", raw_text[:2000], height=200)
                    st.subheader("🧩 Text Chunks Preview")
                    for i, chunk in enumerate(chunks):
                        st.markdown(f"**Chunk {i+1}:**")
                        st.code(chunk, language="markdown")

                except Exception as e:
                    st.error(f"❌ Failed to process PDF: {e}")
        else:
            st.info("📄 Text already extracted.")
            #st.text_area("📖 Preview Extracted Text", st.session_state["pdf_text"][:3000], height=200)
        # 📤 User Query
        user_query = st.text_input("🔎 Ask a question based on this PDF")

        if user_query and st.session_state.get("vectorstore"):
            with st.spinner("🧠 Performing semantic search..."):
                try:
                    # Retrieve top relevant chunks
                    relevant_docs = st.session_state["vectorstore"].similarity_search(user_query, k=3)

                    # Extract and display content
                    for i, doc in enumerate(relevant_docs, 1):
                        st.markdown(f"**Match {i}:**")
                        st.write(doc.page_content)
                        st.markdown("---")

                except Exception as e:
                    st.error(f"❌ Semantic search failed: {e}")

        if st.button("Get IR Answer") and user_query:
            response = st.session_state.ir_agent.run(user_query).messages[-1].content
            st.markdown(f"**Answer:** {response}")

    else:
        st.warning("📥 Please upload a PDF to proceed.")
