import speech_recognition as sr
from difflib import get_close_matches
import pandas as pd
import os
from datetime import datetime
import streamlit as st


def listen_for_name(recognizer, mic):
    with mic as source:
        print("Calibrating for background noise... stay quiet")
        recognizer.adjust_for_ambient_noise(source)

        print("Listening... speak now")
        audio = recognizer.listen(source)
        print("Done listening, processing...")

        try:
            result = recognizer.recognize_google(audio)
            result = result.lower()
            return result
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"API error: {e}")
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
    columns = ["roll_no","name","timestamp"]
    today = datetime.now().date()

    if attendance_file_exists and os.path.getsize(attendance_file) > 0:
       attendance = pd.read_csv(attendance_file)
       attendance['timestamp'] = pd.to_datetime(attendance['timestamp']).dt.date
       already_marked = ((attendance["roll_no"] == matched_row["roll_no"]) & (attendance["timestamp"] == today)).any()

       if not already_marked:
           pd.DataFrame([
           {"roll_no": matched_row["roll_no"],
            "name": matched_row["name"], 
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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]).to_csv(attendance_file, mode="a", header=False, index=False)
        return "created and marked"


@st.cache_data
def load_roaster():
    roster = pd.read_csv("student_roster.csv")
    return roster

st.title("AttendAI — Voice Attendance")

recognizer = sr.Recognizer()
mic = sr.Microphone()
attendance_file = "attendance_log.csv"
roster = load_roaster()

if st.button("Start Session"):
    text = listen_for_name(recognizer, mic)
    if text is None:
        st.error("Could not understand audio")
    else:
        matched_row = match_to_roster(text, roster)
        if matched_row is None:
            st.warning("No student matched")

        else:
            status = mark_attendance(matched_row, attendance_file)
            st.success(f"{matched_row['name']}: {status}")
