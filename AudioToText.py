import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip
from datetime import datetime

# Initialize recognizer
r = sr.Recognizer()

def extract_audio_from_video(video_file_path, output_audio_path):
    
    # Extracts audio from a video file and saves it as a WAV file
    try:
        # Load video file
        video = VideoFileClip(video_file_path)
        
        # Write audio to a file
        video.audio.write_audiofile(output_audio_path, codec='pcm_s16le')  # Ensures it is in WAV format
        
        print(f"Audio extracted to: {output_audio_path}")
        return output_audio_path
    
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

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

def output_text(text, suffix):
    # Generate a unique filename using the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output_{timestamp}.txt"
    
    # Write the recognized text to the file
    with open(filename, "w") as f:
        f.write(text)
    
    print(f"Text written to {filename}")

def remove_filler_words(text):
    filler_words = {"um", "uh", "like", "you know", "basically", "actually", "literally", "so", "kind of", "sort of", "I mean"}
    
    # Split text into words and remove fillers
    words = text.split()
    cleaned_words = [word for word in words if word.lower() not in filler_words]
    
    # Rejoin words into a cleaned text
    return " ".join(cleaned_words)

# Provide the path to your video file here
video_file_path = r"C:\Users\Robert\Documents\UniProject\Python\video\project1.mp4"

# Provide the path to your audio file here
audio_file_path = r"C:\Users\Robert\Documents\UniProject\Python\audio\test.wav"

# Extract audio from the video file
extracted_audio = extract_audio_from_video(video_file_path, audio_file_path)


if extracted_audio:
    # Process the extracted audio file
    recognized_text = process_audio_file(extracted_audio)

    if recognized_text:
        output_text(recognized_text, "original")
        cleaned_text = remove_filler_words(recognized_text)
        output_text(cleaned_text, "cleaned")
        print("Recognized Text:", recognized_text)
        print("Cleaned Text:", cleaned_text)
        
