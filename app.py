import streamlit as st

st.set_page_config(
    page_title="Attendance Bot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Attendance Automation System")

st.markdown("""
### Welcome!
This application automates attendance management using Gemini AI.

**Features:**
- **Upload Attendance**: Paste unstructured attendance text from messaging apps.
- **View Records**: Check and filter attendance history.
- **AI Assistant**: Ask questions about attendance in natural language.

👈 **Select a page from the sidebar to get started.**

---
**Setup Status:**
""")

# Quick setup check
if "supabase" in st.secrets and "url" in st.secrets["supabase"]:
    st.success("✅ Supabase configured")
else:
    st.error("❌ Supabase secrets missing")

if "google" in st.secrets and "api_key" in st.secrets["google"]:
    st.success("✅ Gemini AI configured")
else:
    st.error("❌ Gemini API Key missing")
