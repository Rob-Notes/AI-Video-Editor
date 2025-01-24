import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip
from datetime import datetime
import spacy
import re

# Initialize recognizer
r = sr.Recognizer()

nlp = spacy.load('en_core_web_sm')

# List of filler words
filler_words = ["um", "uh", "like", "you know", "actually", "basically", 
                "seriously", "literally", "honestly", "totally", "just", 
                "right", "so", "okay", "well"]

def extract_audio_from_video(video_file_path, output_audio_path):
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
    filename = f"output_{suffix}_{timestamp}.txt"
    
    # Write the recognized text to the file
    with open(filename, "w") as f:
        f.write(text)
    
    print(f"Text written to {filename}")
    return filename

def remove_filler_words_with_pos(text):
    doc = nlp(text)

    # Filter out words based on their POS tags and the filler word list
    cleaned_text = ' '.join([token.text for token in doc 
                             if token.pos_ not in ['INTJ', 'PART'] and token.text.lower() not in filler_words])

    return cleaned_text

def remove_repetition_and_phrases(text):
    # Remove repeated words in a row (e.g., "I I went" -> "I went")
    words = text.split()
    result = []

    prev_word = None
    for word in words:
        if word != prev_word:  # Only add the word if it's not the same as the previous one
            result.append(word)
        prev_word = word

    # Remove repeated phrases (e.g., "going to send the going to send the transcript" -> "going to send the transcript")
    cleaned_text = ' '.join(result)
    cleaned_text = remove_repeated_phrases_from_text(cleaned_text)

    return cleaned_text

def remove_repeated_phrases_from_text(text):
    # Remove repeated consecutive phrases (e.g., "going to send the going to send the transcript" -> "going to send the transcript")
    words = text.split()
    seen = set()
    result = []
    
    for word in words:
        if word not in seen:
            result.append(word)
            seen.add(word)
    
    return ' '.join(result)

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
        
        # Step 1: Remove filler words
        cleaned_text = remove_filler_words_with_pos(recognized_text)
        
        # Step 2: Remove repetitions and phrases
        cleaned_text_no_repetition = remove_repetition_and_phrases(cleaned_text)
        
        output_text(cleaned_text_no_repetition, "cleaned")
        
        print("Recognized Text:", recognized_text)
        print("Cleaned Text:", cleaned_text_no_repetition)
