import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chatbot import get_chatbot_agent
from utils import require_login

st.set_page_config(page_title="AI Assistant", page_icon="💬")
require_login()

st.title("💬 Attendance Assistant (Groq)")
st.caption("Ask questions like 'Who was absent on Jan 31st?' or 'Mark 59 as Present'.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Output
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent = get_chatbot_agent()
                if agent:
                    response = agent.run(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error("Chatbot agent could not be initialized. Check secrets.")
            except Exception as e:
                st.error(f"Error: {e}")
