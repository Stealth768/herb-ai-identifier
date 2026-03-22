import streamlit as st
import ollama

st.set_page_config(page_title="Herb-AI", page_icon="🌿")

st.title("🌿 Unani & Ayurveda AI Project")
st.write("Current Status: Connecting to RTX 2050...")

# Simple test to see if Ollama is awake
if st.button("Test AI Connection"):
    try:
        response = ollama.chat(model='llama3.2:3b', messages=[
            {'role': 'user', 'content': 'Say hello in a scientific way!'}
        ])
        st.success(f"AI Response: {response['message']['content']}")
    except Exception as e:
        st.error(f"Could not connect to Ollama. Is it running? Error: {e}")