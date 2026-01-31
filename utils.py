import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
from datetime import datetime

# Initialize Supabase
def init_supabase() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
        return None

# Initialize Gemini
def init_gemini():
    try:
        genai.configure(api_key=st.secrets["google"]["api_key"])
    except Exception as e:
        st.error(f"Gemini configuration failed: {e}")

def parse_attendance_text(text: str):
    """
    Uses Gemini to parse the unstructured attendance text into a structured JSON.
    """
    init_gemini()
    model = genai.GenerativeModel('gemini-2.0-flash-exp') 

    prompt = f"""
    You are an assistant that parses attendance records.
    Extract the following from the provided text:
    1. Date: Convert to YYYY-MM-DD format.
    2. Session: 'Morning' or 'Afternoon'.
    3. Section: 'A' or 'B' (look for clues like 'AD-A', 'AD-B', or generally Section A/B). If unsure/not found, return null.
    4. Records: A list of students with their SPECIFIC status (Absent, OD, Late).
    
    Important rules:
    - The text typically lists Absentees, OD (On Duty), and Late comers.
    - Extract the 'register_number' from lines like "59.Mouleeswaran" -> "59".
    - Ignore the names, we rely on register number.
    - Status should be exactly one of: "Absent", "OD", "Late".
    - Do NOT list students who are 'Present'. We will assume anyone not listed is Present.
    
    Return ONLY a valid JSON object with this structure:
    {{
        "date": "YYYY-MM-DD",
        "session": "Morning",
        "section": "B",
        "records": [
            {{ "register_number": "59", "status": "Absent" }},
            {{ "register_number": "87", "status": "OD" }}
        ]
    }}
    
    Input Text:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except Exception as e:
        return {"error": str(e)}

def mark_attendance(supabase: Client, parsed_data: dict):
    """
    Updates the database based on parsed data.
    Assumes all students for the section are 'Present' unless listed otherwise in parsed_data.
    """
    if "error" in parsed_data:
        return {"error": parsed_data["error"]}
        
    date_str = parsed_data.get("date")
    session = parsed_data.get("session")
    section = parsed_data.get("section")
    records = parsed_data.get("records", [])

    if not date_str or not session:
        return {"error": "Could not extract Date or Session from text."}
    
    if not section:
        return {"error": "Could not extract Section (A or B) from text. Please ensure section is mentioned."}

    # 1. Fetch all students in this section to get their IDs
    response_students = supabase.table("students").select("id, register_number").eq("section", section).execute()
    
    if not response_students.data:
        return {"error": f"No student records found for Section {section}. Please populate 'students' table first."}
    
    all_students = {s['register_number']: s['id'] for s in response_students.data}
    
    # 2. Prepare attendance records to upsert
    attendance_upserts = []
    
    # Map parsed records for quick lookup
    parsed_status_map = {r['register_number']: r['status'] for r in records}
    
    for reg_no, student_id in all_students.items():
        # Determine status: Default to 'Present' if not in parsed list
        status = parsed_status_map.get(reg_no, "Present")
        
        attendance_upserts.append({
            "student_id": student_id,
            "date": date_str,
            "session": session,
            "status": status
        })
    
    # 3. Perform upsert
    if attendance_upserts:
        # Supabase upsert requires specifying conflict columns if we want to update
        # We defined UNIQUE(student_id, date, session) in SQL, so on_conflict should work
        try:
            result = supabase.table("attendance").upsert(attendance_upserts, on_conflict="student_id, date, session").execute()
            return {"success": True, "count": len(attendance_upserts), "date": date_str, "session": session, "section": section}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "No records generated."}
