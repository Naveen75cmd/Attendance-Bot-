import streamlit as st
import sys
import os

# Add parent dir to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import parse_attendance_text, mark_attendance, init_supabase

st.set_page_config(page_title="Upload Attendance", page_icon="📝")

st.title("📝 Upload Attendance")

st.markdown("""
Paste the attendance text below. The AI will extract:
- **Date**
- **Session**
- **Section**
- **Absentees, OD, Late** (Assume others are Present - *Requires Student DB to be populated*)
""")

attendance_text = st.text_area("Paste Attendance Text Here", height=300, placeholder="31 Jan 2026\nMorning attendance\nAD-B\n...")

if st.button("Process Attendance"):
    if not attendance_text:
        st.warning("Please paste some text first.")
    else:
        with st.spinner("AI is parsing the text..."):
            result = parse_attendance_text(attendance_text)
        
        if "error" in result:
            st.error(f"AI Parsing Error: {result['error']}")
        else:
            st.success("Parsing Successful!")
            st.json(result)
            
            # Confirm Upload
            if st.button("Confirm and Save to Database"): 
                # Note: Nested buttons don't work well in Streamlit.
                # Usually we use session state or move this out.
                pass 
            
            # Better pattern: Use session state to store parsed result, then show Save button
            st.session_state['parsed_data'] = result

if 'parsed_data' in st.session_state:
    st.info("Review the data above. If correct, click Save.")
    if st.button("Save to Database"):
        supabase = init_supabase()
        if supabase:
            with st.spinner("Saving to Supabase..."):
                save_result = mark_attendance(supabase, st.session_state['parsed_data'])
                
            if "error" in save_result:
                st.error(f"Database Error: {save_result['error']}")
            else:
                st.success(f"Saved! {save_result['count']} records updated for {save_result['section']} - {save_result['date']} ({save_result['session']}).")
                del st.session_state['parsed_data'] # Clear state
