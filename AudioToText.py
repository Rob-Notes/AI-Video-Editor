from moviepy import VideoFileClip, concatenate_videoclips
import speech_recognition as sr
<<<<<<< HEAD
import spacy
from datetime import datetime
import re
import numpy as np
=======
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy import VideoFileClip, concatenate_videoclips
from datetime import datetime
import spacy
import whisper

>>>>>>> 73055941f9e4e9779d4d35f65958e550d47f885d

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

<<<<<<< HEAD
            # Use Google to recognize audio
            MyText = r.recognize_google(audio_data, show_all=True)

            # Extract transcript and timestamps
            if isinstance(MyText, dict) and 'alternative' in MyText:
                transcript = MyText['alternative'][0]['transcript']
                return transcript
            else:
                return MyText
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio")
=======
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
>>>>>>> 73055941f9e4e9779d4d35f65958e550d47f885d

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

<<<<<<< HEAD
def detect_silence(audio_clip, silence_threshold=-40.0, min_silence_duration=0.5):
    """
    Detects silence in an audio clip.
    """
    audio = audio_clip.to_soundarray(fps=44100)  # Convert to numpy array
    audio = audio.mean(axis=1)  # Convert stereo to mono
    audio_db = 20 * np.log10(np.abs(audio) + 1e-6)  # Convert to dB

    # Find silent segments
    silent_segments = []
    is_silent = False
    start_time = 0

    for i, db in enumerate(audio_db):
        if db < silence_threshold and not is_silent:
            is_silent = True
            start_time = i / 44100  # Convert sample index to time
        elif db >= silence_threshold and is_silent:
            is_silent = False
            end_time = i / 44100
            if end_time - start_time >= min_silence_duration:
                silent_segments.append((start_time, end_time))

    return silent_segments

def identify_low_importance_segments(original_text, video_clip):
    """
    Identifies low-importance segments in the video based on text analysis.
    """
    # Split the original text into sentences
    doc = nlp(original_text)
    sentences = [sent.text for sent in doc.sents]

    # Define criteria for low-importance content
    low_importance_segments = []
    current_time = 0
    word_duration = video_clip.duration / len(original_text.split())  # Approximate duration per word

    for sentence in sentences:
        # Criteria 1: Short sentences (less than 5 words)
        if len(sentence.split()) < 5:
            start_time = current_time
            end_time = start_time + (len(sentence.split()) * word_duration)
            low_importance_segments.append((start_time, end_time))

        # Criteria 2: Non-essential phrases (e.g., greetings, casual remarks)
        non_essential_phrases = ["hi", "hello", "thank you", "thanks", "anyway", "well", "so"]
        if any(phrase in sentence.lower() for phrase in non_essential_phrases):
            start_time = current_time
            end_time = start_time + (len(sentence.split()) * word_duration)
            low_importance_segments.append((start_time, end_time))

        # Update current_time for the next sentence
        current_time += len(sentence.split()) * word_duration

    return low_importance_segments

def identify_unimportant_segments(original_text, cleaned_text, video_clip):
    """
    Identifies segments of the video that are unimportant and can be cut.
    """
    # Split the original and cleaned text into words
    original_words = original_text.split()
    cleaned_words = cleaned_text.split()

    # Find repeated phrases in the original text
    repeated_phrases = []
    for i in range(len(original_words)):
        for j in range(i + 1, len(original_words)):
            if original_words[i] == original_words[j]:
                # Check if the next few words also match (to identify phrases)
                phrase_length = 1
                while (i + phrase_length < len(original_words) and
                       j + phrase_length < len(original_words) and
                       original_words[i + phrase_length] == original_words[j + phrase_length]):
                    phrase_length += 1

                if phrase_length > 1:  # Only consider phrases longer than 1 word
                    repeated_phrases.append((i, i + phrase_length, j, j + phrase_length))

    # Identify the time segments to remove
    segments_to_remove = []
    current_time = 0
    word_duration = video_clip.duration / len(original_words)  # Approximate duration per word

    # Add repeated phrases to segments_to_remove
    for phrase in repeated_phrases:
        start1, end1, start2, end2 = phrase
        # Remove the second occurrence of the repeated phrase
        segments_to_remove.append((start2 * word_duration, end2 * word_duration))

    # Detect silence and add to segments_to_remove
    silent_segments = detect_silence(video_clip.audio)
    segments_to_remove.extend(silent_segments)

    # Detect low-importance content and add to segments_to_remove
    low_importance_segments = identify_low_importance_segments(original_text, video_clip)
    segments_to_remove.extend(low_importance_segments)

    return segments_to_remove

def edit_video(video_clip, segments_to_remove):
    """
    Edits the video by removing the specified segments.
    """
    # Sort segments by start time
    segments_to_remove.sort()

    # Create a list of video clips to keep
    clips_to_keep = []
    start_time = 0

    for segment in segments_to_remove:
        segment_start, segment_end = segment
        if start_time < segment_start:
            # Add the segment before the removed part
            clips_to_keep.append(video_clip.subclipped(start_time, segment_start))
        start_time = segment_end

    # Add the remaining part of the video
    if start_time < video_clip.duration:
        clips_to_keep.append(video_clip.subclipped(start_time, video_clip.duration))

    # Concatenate the remaining clips
    final_clip = concatenate_videoclips(clips_to_keep)
    return final_clip
=======
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
>>>>>>> 73055941f9e4e9779d4d35f65958e550d47f885d

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

<<<<<<< HEAD
    if recognized_text:
        output_text(recognized_text, "original")
        
        # Step 1: Remove filler words
        cleaned_text = remove_filler_words_with_pos(recognized_text)
        
        # Step 2: Remove repetitions and phrases
        cleaned_text_no_repetition = remove_repetition_and_phrases(cleaned_text)
        
        output_text(cleaned_text_no_repetition, "cleaned")
        
        print("Recognized Text:", recognized_text)
        print("Cleaned Text:", cleaned_text_no_repetition)

        # Step 3: Identify unimportant segments
        video_clip = VideoFileClip(video_file_path)
        segments_to_remove = identify_unimportant_segments(recognized_text, cleaned_text_no_repetition, video_clip)

        # Step 4: Edit the video
        final_clip = edit_video(video_clip, segments_to_remove)

        # Save the edited video
        output_video_path = r"C:\Users\Robert\Documents\UniProject\Python\video\edited_project1.mp4"
        final_clip.write_videofile(output_video_path, codec="libx264")

        print(f"Edited video saved to: {output_video_path}")
=======
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
>>>>>>> 73055941f9e4e9779d4d35f65958e550d47f885d
