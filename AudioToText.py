import speech_recognition as sr
import pyttsx3
from datetime import datetime

# Initialize recognizer
r = sr.Recognizer()

def process_audio_file(audio_file_path):
    try:
        # Load the audio file
        with sr.AudioFile(audio_file_path) as source:
            # Prepare recognizer to process the file
            audio_data = r.record(source)

            # Use Google to recognize audio
            MyText = r.recognize_google(audio_data)

            return MyText

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio")

def output_text(text):
    # Generate a unique filename using the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output_{timestamp}.txt"
    
    # Write the recognized text to the file
    with open(filename, "w") as f:
        f.write(text)
    
    print(f"Text written to {filename}")

# Provide the path to your audio file here
audio_file_path = r"C:\Users\Robert\Documents\UniProject\Python\audio\test.wav"

# Process the audio file
recognized_text = process_audio_file(audio_file_path)

if recognized_text:
    output_text(recognized_text)
    print("Recognized Text:", recognized_text)
