import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy import VideoFileClip, concatenate_videoclips
from datetime import datetime
import spacy
import whisper


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
    # Load the Whisper model (you can choose 'tiny', 'base', 'small', 'medium', or 'large')
    model = whisper.load_model("base")  # Adjust the model size as needed

    # Transcribe the audio file
    result = model.transcribe(audio_file_path)

    # Extract the transcript and timestamps
    segments = []
    for segment in result["segments"]:
        segments.append({
            "text": segment["text"],
            "start": segment["start"],
            "end": segment["end"]
        })
    
    print(f"Transcription completed. Text: {result['text'][:100]}...")  # Print a snippet of the transcription
    return segments

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

def filter_segments(segments, cleaned_text):
    filtered_segments = []
    for segment in segments:
        if any(cleaned_sentence in segment['text'] for cleaned_sentence in cleaned_text.split('.')):
            filtered_segments.append(segment)
    return filtered_segments

def cut_video(video_path, segments, output_path):
    video = VideoFileClip(video_path)
    clips = []
    for segment in segments:
        clip = video.subclip(segment['start'], segment['end'])
        clips.append(clip)
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path, codec="libx264")

# Provide the path to your video file here
video_file_path = r"C:\Users\Robert\Documents\UniProject\Python\video\project1.mp4"

# Provide the path to your audio file here
audio_file_path = r"C:\Users\Robert\Documents\UniProject\Python\audio\test.wav"

# Extract audio from the video file
extracted_audio = extract_audio_from_video(video_file_path, audio_file_path)

# Process the extracted audio with Whisper
if extracted_audio:
    # Recognize audio with timestamps using Whisper
    segments = process_audio_file(extracted_audio)

    # Reconstruct the recognized text
    recognized_text = ' '.join([seg['text'] for seg in segments])

    # Output original transcription
    output_text(recognized_text, "original")

    # Clean text
    cleaned_text = remove_filler_words_with_pos(recognized_text)
    cleaned_text_no_repetition = remove_repetition_and_phrases(cleaned_text)

    # Output cleaned transcription
    output_text(cleaned_text_no_repetition, "cleaned")

    # Filter segments based on cleaned text
    filtered_segments = filter_segments(segments, cleaned_text_no_repetition)

    # Cut video based on filtered segments
    cut_video(video_file_path, filtered_segments, r"C:\Users\Robert\Documents\UniProject\Python\video\output.mp4")

    print("Video trimmed successfully.")
