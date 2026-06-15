import speech_recognition as sr
from difflib import get_close_matches
import pandas as pd
import os
from datetime import datetime

roster = pd.read_csv("student_roster.csv")
names = roster["name"].str.lower()




recognizer = sr.Recognizer()
mic = sr.Microphone()
with mic as source:
    print("Calibrating for background noise... stay quiet")
    recognizer.adjust_for_ambient_noise(source)

    print("Listening... speak now")
    audio = recognizer.listen(source)
    print("Done listening, processing...")

    try:
        result = recognizer.recognize_google(audio)
        result = result.lower()
        print(result)
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"API error: {e}")


        
match = get_close_matches(result, names.tolist(), n=1, cutoff=0.5)
if match:
    matching_rows = roster[roster["name"].str.lower() == match[0]]
    roll_number = matching_rows.iloc[0]["roll_no"]
    name = match[0]
    print(name, roll_number)
else:
    print("No match!")

