import speech_recognition as sr

recognizer = sr.Recognizer()
mic = sr.Microphone()
with mic as source:
    recognizer.adjust_for_ambient_noise(source)
    audio = recognizer.listen(source)
    result = recognizer.recognize_google(audio)
    print(result)
