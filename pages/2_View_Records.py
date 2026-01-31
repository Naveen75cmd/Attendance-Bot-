import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import init_supabase

st.set_page_config(page_title="View Records", page_icon="📊", layout="wide")

st.title("📊 Attendance Records")

supabase = init_supabase()

if not supabase:
    st.stop()

# Filters
col1, col2 = st.columns(2)
with col1:
    selected_date = st.date_input("Filter by Date", value=None)
with col2:
    selected_section = st.selectbox("Filter by Section", ["All", "A", "B"])

# Fetch Data
query = supabase.table("attendance").select("*, students(register_number, full_name, section)")

if selected_date:
    query = query.eq("date", selected_date)

# Execute query to get Attendance Data
response = query.execute()

if response.data:
    # Transform for display
    data = []
    for record in response.data:
        student = record['students']
        # Apply Section Filter (Supabase join filtering is tricky, easier to filter in creating list if dataset small)
        if selected_section != "All" and student['section'] != selected_section:
            continue
            
        data.append({
            "Date": record['date'],
            "Session": record['session'],
            "Register No": student['register_number'],
            "Name": student['full_name'],
            "Section": student['section'],
            "Status": record['status']
        })
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download CSV",
            csv,
            "attendance_records.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.info("No records found for the selected filters.")
else:
    st.info("No attendance records found.")

st.markdown("---")
st.subheader("Student Database")
# Quick view of students
if st.checkbox("Show Student List"):
    students_res = supabase.table("students").select("*").execute()
    if students_res.data:
        st.dataframe(pd.DataFrame(students_res.data))
    else:
        st.warning("No students found in database. Please upload student data via SQL or Supabase Dashboard.")
