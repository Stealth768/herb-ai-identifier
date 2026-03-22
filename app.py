import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import os
from duckduckgo_search import DDGS


if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "last_identified" not in st.session_state:
    st.session_state.last_identified = None


API_KEY = "AIzaSyAdyB7i4UyXyiNge4s3JMJdRTGA7FPE8Xw" 
genai.configure(api_key=API_KEY)

SYSTEM_INSTRUCTION = """
You are a senior botanical expert for Unani and Ayurveda. 
Identify the herb from images. If 'Internal Research' text is provided from the knowledge base, 
prioritize that specific data over your general training.
"""

model = genai.GenerativeModel(
    model_name='gemini-3-flash-preview',
    system_instruction=SYSTEM_INSTRUCTION
)

if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])



def get_local_knowledge(herb_name):
    """Searches data/knowledge_base/ for .txt files"""
    clean_name = herb_name.lower().replace(" ", "_").strip()
    kb_path = os.path.join("data", "knowledge_base")
    
    if os.path.exists(kb_path):
        for filename in os.listdir(kb_path):
            if clean_name in filename.lower():
                with open(os.path.join(kb_path, filename), "r", encoding="utf-8") as f:
                    return f.read()
    return None

def get_all_library_files():
    """Lists all files in the knowledge base for the Library tab"""
    kb_path = os.path.join("data", "knowledge_base")
    files_data = []
    if os.path.exists(kb_path):
        for filename in os.listdir(kb_path):
            if filename.endswith(".txt"):
               
                pretty_name = filename.replace(".txt", "").replace("_", " ").title()
                files_data.append({"Herb Name": pretty_name, "File Name": filename})
    return files_data

def get_web_images(herb_name):
    try:
        with DDGS() as ddgs:
            results = ddgs.images(f"{herb_name} medicinal plant botanical", max_results=3)
            return [r['image'] for r in results]
    except:
        return []


st.set_page_config(page_title="Herb-AI Master", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .report-card { background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid #1b5e20; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .lib-card { background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 5px; border: 1px solid #c8e6c9; }
    </style>
    """, unsafe_allow_html=True)


with st.sidebar:
    st.title("🍀 Project Control")
    if st.button("🗑️ Reset Conversation"):
        st.session_state.messages = []
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.last_identified = None
        st.rerun()
    st.divider()
    st.info(f"Files in Knowledge Base: {len(get_all_library_files())}")


st.title("🌿 Herb-AI: Botanical Identification System")

tab_scan, tab_library = st.tabs(["🔍 Live Analysis", "📚 Library"])

with tab_scan:
    col_chat, col_dash = st.columns([2, 1])

    with col_chat:
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])

        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
        
        if prompt := st.chat_input("Ask about a herb..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                st.chat_message("user").write(prompt)

            with chat_container:
                with st.chat_message("assistant"):
                    if uploaded_file and len(st.session_state.messages) <= 2:
                        img = Image.open(uploaded_file).convert('RGB')
                        response = st.session_state.chat_session.send_message([prompt, img])
                    else:
                        response = st.session_state.chat_session.send_message(prompt)
                    
                    name = response.text.split('\n')[0].replace("**", "").strip()
                    st.session_state.last_identified = name

                    local_info = get_local_knowledge(name)
                    if local_info:
                        st.toast(f"Matched {name} in Knowledge Base!")
                        refined = st.session_state.chat_session.send_message(f"Using our internal research: {local_info}. Combine this with your analysis.")
                        final_text = refined.text
                    else:
                        final_text = response.text

                    st.markdown(final_text)
                    st.session_state.messages.append({"role": "assistant", "content": final_text})

    with col_dash:
        st.subheader(" Diagnostic View")
        if st.session_state.last_identified:
            name = st.session_state.last_identified
            st.markdown(f"<div class='report-card'><b>Current Specimen:</b><br>{name}</div>", unsafe_allow_html=True)
            
            st.write("####  Field References")
            urls = get_web_images(name)
            if urls:
                for url in urls:
                    st.image(url, use_container_width=True)

with tab_library:
    st.subheader("Library Index")
    st.write("Scanning...")
    
    library_files = get_all_library_files()
    
    if library_files:
        
        for item in library_files:
            with st.expander(f"📄 {item['Herb Name']}"):
                content = get_local_knowledge(item['Herb Name'])
                st.text_area("File Content", value=content, height=150, disabled=True)
    else:
        st.warning("⚠️ No .txt files found in `data/knowledge_base/`.")