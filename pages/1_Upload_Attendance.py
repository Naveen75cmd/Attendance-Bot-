import streamlit as st
import sys
import os

# Add parent dir to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import parse_attendance_text, mark_attendance, init_supabase, extract_text_from_image, require_login

st.set_page_config(page_title="Upload Attendance", page_icon="📝")
require_login()

st.title("📝 Upload Attendance")

st.markdown("""
**Methods**:
1. 📸 **Upload Screenshot**: Use OCR to extract text from an image.
2. 📋 **Paste Text**: Directly paste the attendance message.
""")

tab1, tab2 = st.tabs(["📸 Upload Image", "📋 Paste Text"])

attendance_text = ""

# TAB 1: Image Upload
with tab1:
    uploaded_file = st.file_uploader("Choose an image (screenshot)...", type=['png', 'jpg', 'jpeg'])
    if uploaded_file is not None:
        if st.button("Extract Text from Image"):
            with st.spinner("Scanning image with OCR Space..."):
                extracted = extract_text_from_image(uploaded_file)
                if extracted.startswith("Error") or extracted.startswith("OCR Error"):
                    st.error(extracted)
                else:
                    st.success("Text Extracted!")
                    # Store in session state to pass to text area or processing
                    st.session_state['extracted_text'] = extracted

    if 'extracted_text' in st.session_state:
        st.subheader("Extracted Text")
        attendance_text = st.text_area("Edit text if needed:", st.session_state['extracted_text'], height=200, key="ocr_text_area")

# TAB 2: Paste Text
with tab2:
    # If we didn't get text from OCR (or user ignores it), use this text area
    # Note: Streamlit widgets with same key conflict. 
    manual_text = st.text_area("Paste Attendance Text Here", height=300, placeholder="31 Jan 2026\nMorning attendance...", key="manual_paste_area")
    if not attendance_text:
        attendance_text = manual_text

st.markdown("---")

if st.button("Process Attendance"):
    if not attendance_text:
        st.warning("Please provide attendance text (via Image or Paste).")
    else:
        with st.spinner("AI is parsing the data..."):
            result = parse_attendance_text(attendance_text)
        
        if "error" in result:
            st.error(f"AI Parsing Error: {result['error']}")
        else:
            st.success("Parsing Successful!")
            st.json(result)
            st.session_state['parsed_data'] = result

if 'parsed_data' in st.session_state:
    st.info("Review the data above. If correct, click Save.")
    if st.button("Confirm and Save to Database"):
        supabase = init_supabase()
        if supabase:
            with st.spinner("Saving to Supabase..."):
                save_result = mark_attendance(supabase, st.session_state['parsed_data'])
                
            if "error" in save_result:
                st.error(f"Database Error: {save_result['error']}")
            else:
                st.success(f"Saved! {save_result['count']} records updated for {save_result['section']} - {save_result['date']} ({save_result['session']}).")
                # Clear states
                if 'parsed_data' in st.session_state: del st.session_state['parsed_data']
                if 'extracted_text' in st.session_state: del st.session_state['extracted_text']
