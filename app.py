import streamlit as st

st.set_page_config(
    page_title="Attendance Bot",
    page_icon="🤖",
    layout="wide"
)

from utils import require_login
require_login()

st.title("🤖 Attendance Automation System")

st.markdown("""
### Welcome!
This application automates attendance management using **OCR and Pattern Matching**.

**Features:**
- **Upload Attendance**: Upload text or images. (OCR by OCR Space, Parsing by Regex).
- **View Records**: Check and filter attendance history.
- **Search Records**: Search for students or specific dates.

👈 **Select a page from the sidebar to get started.**

---
**Setup Status:**
""")

# Quick setup check
if "supabase" in st.secrets and "url" in st.secrets["supabase"]:
    st.success("✅ Supabase configured")
else:
    st.error("❌ Supabase secrets missing")

if "ocr_space" in st.secrets and "api_key" in st.secrets["ocr_space"]:
    st.success("✅ OCR Space configured")
else:
    st.error("❌ OCR Space API Key missing")
