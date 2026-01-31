import streamlit as st
from supabase import create_client, Client
import requests
import re
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

def login_user(email, password):
    """
    Authenticates user with Supabase Auth.
    """
    supabase = init_supabase()
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        return {"error": str(e)}

def require_login():
    """
    Gatekeeper function. Call this at the start of every page.
    If not logged in, shows login form and stops execution.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Login Required")
        
        col1, col2 = st.columns([1, 2])
        with col1:
             st.info("Please sign in to access the Attendance System.")
             
        with col2:
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if st.button("Sign In"):
                if email and password:
                    with st.spinner("Authenticating..."):
                        response = login_user(email, password)
                        if isinstance(response, dict) and "error" in response:
                            st.error(f"Login failed: {response['error']}")
                        elif response and response.user:
                             st.session_state["authenticated"] = True
                             st.session_state["user_email"] = response.user.email
                             st.success("Logged in successfully!")
                             st.rerun()
                else:
                    st.warning("Please enter both email and password.")
        
        st.stop() # Prevent the rest of the app from loading
    
    # Optional: Sidebar logout button
    with st.sidebar:
        st.write(f"👤 {st.session_state.get('user_email', 'User')}")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

def extract_text_from_image(image_file) -> str:
    """
    Uploads image to OCR Space API and returns extracted text.
    """
    if "ocr_space" not in st.secrets:
        return "Error: OCR Space API Key missing in secrets."
    
    api_key = st.secrets["ocr_space"]["api_key"]
    
    try:
        # OCR Space API endpoint
        url = "https://api.ocr.space/parse/image"
        
        payload = {
            'apikey': api_key,
            'language': 'eng',
            'isOverlayRequired': False,
            'detectOrientation': True,
            'scale': True,
            'OCREngine': 2 
        }
        
        # Determine file type (Streamlit returns BytesIO-like object)
        files = {
            'file': (image_file.name, image_file.getvalue(), image_file.type)
        }
        
        response = requests.post(url, files=files, data=payload)
        result = response.json()
        
        if result.get("IsErroredOnProcessing"):
            return f"OCR Error: {result.get('ErrorMessage')}"
            
        parsed_results = result.get("ParsedResults")
        if parsed_results:
            return parsed_results[0].get("ParsedText", "")
        else:
            return "No text found in image."
            
    except Exception as e:
        return f"OCR Request Failed: {str(e)}"

def parse_attendance_text(text: str):
    """
    Parses attendance text using REGEX (Rule-based) instead of AI.
    """
    
    # 1. Normalize text
    # Replace common OCR errors or spacing issues could happen, but let's stick to basic regex first.
    lines = text.split('\n')
    
    data = {
        "date": None,
        "session": None,
        "section": None,
        "records": []
    }
    
    # REGEX PATTERNS
    
    # Date: Matches DD Jan YYYY or DD-MM-YYYY
    # Example: 31 Jan 2026
    date_pattern = r"(\d{1,2})[\s\.\-\/]+([A-Za-z]{3,9})[\s\.\-\/]+(\d{4})" 
    
    # Session: Morning or Afternoon
    session_pattern = r"(Morning|Afternoon)"
    
    # Section: AD-A, AD-B, Section A, Section B
    # We look for "-A" or "-B" or " A" / " B" near keywords like AD or Section
    section_pattern_broad = r"(AD|Section)[\s-]*([AB])"
    
    # Categories Keywords
    cat_absent = r"(Absentees|Absent)"
    cat_od = r"(OD|On Duty)"
    cat_late = r"(Late|Late comers)"
    
    current_category = "Absent" # Default assumption if numbers appear early? No, usually sections have headers.
    
    # SEARCH FOR METADATA GLOBALLY FIRST
    
    # Date
    date_match = re.search(date_pattern, text, re.IGNORECASE)
    if date_match:
        try:
            day, month_str, year = date_match.groups()
            # Parse date string to object then back to ISO YYYY-MM-DD
            # Handle standard 3-letter months
            date_obj = datetime.strptime(f"{day}-{month_str[:3]}-{year}", "%d-%b-%Y")
            data["date"] = date_obj.strftime("%Y-%m-%d")
        except:
            # Fallback or try other formats if complex
            pass
            
    # Session
    session_match = re.search(session_pattern, text, re.IGNORECASE)
    if session_match:
        # Standardize case
        sess = session_match.group(1).lower()
        data["session"] = "Morning" if "morning" in sess else "Afternoon"
        
    # Section
    section_match = re.search(section_pattern_broad, text, re.IGNORECASE)
    if section_match:
        data["section"] = section_match.group(2).upper()
        
    # PARSE RECORDS LINE BY LINE
    # We detect when we enter a "Block" (Absent, OD, Late)
    # Then we look for register numbers "69.Name" -> 69
    
    active_status = None # None means we haven't hit a header yet
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Check for Headers
        if re.search(cat_absent, line_clean, re.IGNORECASE):
            active_status = "Absent"
            continue
        elif re.search(cat_od, line_clean, re.IGNORECASE):
            active_status = "OD"
            continue
        elif re.search(cat_late, line_clean, re.IGNORECASE):
            active_status = "Late"
            continue
        elif "Present" in line_clean or "Total" in line_clean:
            active_status = None # Reset if we hit summary lines
            continue
            
        # extract_students
        if active_status:
            # Look for "digits dot" pattern e.g. "59." or just "59" at start of line
            # Strict mode: Number followed by dot or space and letters
            # Regex: Start of line, digits, dot or space
            student_match = re.match(r"^(\d+)", line_clean)
            if student_match:
                reg_no = student_match.group(1)
                data["records"].append({
                    "register_number": reg_no,
                    "status": active_status
                })

    return data

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
        return {"error": "Could not extract Date or Session from text. Please ensure format is 'DD MMM YYYY' and 'Morning/Afternoon'."}
    
    if not section:
        return {"error": "Could not extract Section (A or B) from text. keys like 'AD-A' or 'AD-B' are expected."}

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
        try:
            result = supabase.table("attendance").upsert(attendance_upserts, on_conflict="student_id, date, session").execute()
            return {"success": True, "count": len(attendance_upserts), "date": date_str, "session": session, "section": section}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "No records generated."}
