import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import init_supabase, require_login

st.set_page_config(page_title="View Records", page_icon="📊", layout="wide")
require_login()

st.title("📊 View Attendance Records")

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


tab1, tab2 = st.tabs(["📝 Detailed Records", "📈 Attendance Percentage"])

with tab1:
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
            st.dataframe(df, width="stretch")
            
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

with tab2:
    st.subheader("Student Attendance Statistics")
    
    # Fetch ALL data for stats (ignore date filter usually, but maybe keep section)
    # If date filter is active, stats are for that period.
    
    if data: # reuse fetch
        df_stats = pd.DataFrame(data)
        
        # Group by Student
        stats = []
        students_group = df_stats.groupby("Register No")
        
        for reg_no, group in students_group:
            total_sessions = len(group)
            # Present + OD + Late = Present for percentage purposes
            present_count = len(group[group['Status'].isin(['Present', 'OD', 'Late'])])
            absent_count = len(group[group['Status'] == 'Absent'])
            perc = (present_count / total_sessions) * 100 if total_sessions > 0 else 0
            
            stats.append({
                "Register No": reg_no,
                "Name": group.iloc[0]["Name"],
                "Total Sessions": total_sessions,
                "Present": present_count,
                "Absent": absent_count,
                "Attendance %": round(perc, 2)
            })
            
        df_summary = pd.DataFrame(stats)
        st.dataframe(df_summary, use_container_width=True)
        
        st.markdown("**Formula used:** `(Present + OD + Late) / Total Sessions * 100`")
    else:
        st.info("No data to calculate statistics.")

st.markdown("---")
st.subheader("Student Database")
# Quick view of students
if st.checkbox("Show Student List"):
    students_res = supabase.table("students").select("*").execute()
    if students_res.data:
        st.dataframe(pd.DataFrame(students_res.data))
    else:
        st.warning("No students found in database. Please upload student data via SQL or Supabase Dashboard.")
