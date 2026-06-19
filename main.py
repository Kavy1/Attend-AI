import speech_recognition as sr
from difflib import get_close_matches
import pandas as pd
import os
from datetime import datetime
import streamlit as st


def listen_for_name(recognizer, mic):
    status_box = st.empty()
    with mic as source:
        status_box.info("Calibrating for background noise... stay quiet")
        recognizer.adjust_for_ambient_noise(source)

        status_box.info("Listening now, Please speak!")
        audio = recognizer.listen(source)
        status_box.info("Done listening, processing...")

        try:
            result = recognizer.recognize_google(audio)
            status_box.empty()
            result = result.lower()
            return result
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            st.error(f"API error: {e}")
            return None

def match_to_roster(text, roster):
    match = get_close_matches(text, roster["name"].str.lower().tolist(), n=1, cutoff=0.5)
    if match:
        matching_rows = roster[roster["name"].str.lower() == match[0]].iloc[0]
        return matching_rows
    else:
        return None

def mark_attendance(matched_row, attendance_file):

    attendance_file_exists = os.path.exists(attendance_file)
    columns = ["roll_no","name","status","timestamp"]
    today = datetime.now().date()

    if attendance_file_exists and os.path.getsize(attendance_file) > 0:
       attendance = pd.read_csv(attendance_file)
       attendance['timestamp'] = pd.to_datetime(attendance['timestamp']).dt.date
       already_marked = ((attendance["roll_no"] == matched_row["roll_no"]) & (attendance["timestamp"] == today)).any()

       if not already_marked:
           pd.DataFrame([
           {"roll_no": matched_row["roll_no"],
            "name": matched_row["name"], 
            "status": "P",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_csv(attendance_file, mode="a", header=False, index=False)
           return "marked"
       else:
           return "duplicate"
    else: 
        attendance = pd.DataFrame(columns=columns)
        attendance.to_csv(attendance_file, index=False)
        pd.DataFrame([
           {"roll_no": matched_row["roll_no"],
            "name": matched_row["name"], 
            "status": "P",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_csv(attendance_file, mode="a", header=False, index=False)
        return "created and marked"

def get_todays_attendance(attendance_file):
    today = datetime.now().date()
    attendance_file_exists = os.path.exists(attendance_file)
    if attendance_file_exists and os.path.getsize(attendance_file) > 0:
        attendance = pd.read_csv(attendance_file)
        attendance['timestamp'] = pd.to_datetime(attendance['timestamp']).dt.date
        filtered_attendance = attendance[attendance['timestamp'] == today]
        print(filtered_attendance)
        return filtered_attendance.sort_values(by="roll_no")                               
    else:
        attendance = pd.DataFrame(columns=["roll_no","name","status","timestamp"])
        return attendance
    
def end_session(roster, attendance_file):
    today = datetime.now().date()
    sorted_roster = roster.sort_values(by="roll_no")
    already_today = get_todays_attendance(attendance_file)
    present_today = already_today[already_today["status"] == "P"]

    new_rows = []

    for _, student in sorted_roster.iterrows():
        already_has_row = student["roll_no"] in already_today["roll_no"].values
        
        if not already_has_row:
            is_present = student["roll_no"] in present_today["roll_no"].values
            new_rows.append({
                "roll_no": student["roll_no"],
                "name": student["name"],
                "status": "P" if is_present else "A",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    if new_rows:
        pd.DataFrame(new_rows).to_csv(attendance_file, mode="a", header=False, index=False)
        return "session ended"
    else:
        return "already ended"
  

@st.cache_data
def load_roaster():
    roster = pd.read_csv("student_roster.csv")
    return roster


st.title("AttendAI — Voice Attendance")

recognizer = sr.Recognizer()
mic = sr.Microphone()
attendance_file = "attendance_log.csv"
roster = load_roaster()

st.subheader("Class Roster")
st.dataframe(roster, hide_index=True)


if st.button("Start Session"):
    text = listen_for_name(recognizer, mic)
    
    if text is None:
        print("No detection")
        st.error("Could not understand audio")
    else:
        matched_row = match_to_roster(text, roster)
        if matched_row is None:
            st.warning("No student matched")
            print("No matching")

        else:
            status = mark_attendance(matched_row, attendance_file)
            st.success(f"{matched_row['name']}: {status}")

if st.button("End Session"):
    status = end_session(roster, attendance_file)
    st.success("Session ended — absences recorded")
    st.subheader("Today's Attendance")
    st.dataframe(get_todays_attendance(attendance_file), hide_index=True)