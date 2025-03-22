import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from moviepy import VideoFileClip, concatenate_videoclips
import whisper
import threading
from openai import OpenAI

#initialise whisper model
whisperModel = whisper.load_model("base")

#filler word list
fillerWords = ["um", "uh", "like", "you know", "actually", "basically", "seriously", "literally"]

#initialise openai client
openAIClient = OpenAI(api_key="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")  # Replace with your OpenAI API key

#function to extract audio from video
def extractAudio(videoFilePath, audioOutputPath):
    try:
        video = VideoFileClip(videoFilePath)
        video.audio.write_audiofile(audioOutputPath, codec='pcm_s16le')
        return audioOutputPath
    except Exception as e:
        messagebox.showerror("Error", f"Error extracting audio: {e}")
        return None

#function to transcribe audio
def transcribeAudio(audioFilePath):
    result = whisperModel.transcribe(audioFilePath, word_timestamps=True)
    transcript = result["text"]
    timestamps = []
    for segment in result["segments"]:
        for word in segment["words"]:
            wordText = word["word"]
            wordStartTime = word["start"]
            wordEndTime = word["end"]
            timestamps.append({"word": wordText, "start": wordStartTime, "end": wordEndTime})
    return transcript, timestamps

#function to detect repeated phrases
def detectRepetition(transcript, timestamps, minPhraseLength=3):
    words = transcript.split()
    repeatedPhrases = []
    for i in range(len(words) - minPhraseLength + 1):
        phrase1 = " ".join(words[i:i + minPhraseLength])
        for j in range(i + 1, len(words) - minPhraseLength + 1):
            phrase2 = " ".join(words[j:j + minPhraseLength])
            if phrase1 == phrase2:
                repeatedPhrases.append((i, i + minPhraseLength, j, j + minPhraseLength))
    segmentsToRemove = []
    for phrase in repeatedPhrases:
        start1, end1, start2, end2 = phrase
        phraseStart = timestamps[start2]["start"]
        phraseEnd = timestamps[end2 - 1]["end"]
        segmentsToRemove.append((phraseStart, phraseEnd))
    return segmentsToRemove

#function to identify unimportant segments using chatgpt
def identifyUnimportantContentChatGPT(transcript, timestamps):
    
    #prepare prompt
    prompt = f"""
    Below is a transcript of a video. Identify the timestamps of any unimportant content (e.g., tangents, off-topic discussions) that should be removed. 
    Return the timestamps in the format: [(start1, end1), (start2, end2), ...].

    Transcript:
    {transcript}

    Timestamps:
    {timestamps}

    Return only the timestamps of unimportant content. Do not rephrase or summarize the transcript.
    """

    #send prompt to chatgpt
    response = openAIClient.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )

    #get response
    chatGPTOutput = response.choices[0].message.content.strip()

    try:
        segmentsToRemove = eval(chatGPTOutput)
        return segmentsToRemove
    except Exception as e:
        print(f"Error parsing LLM output: {e}")
        return []

#function to identify unimportant segments
def identifyOtherUnimportantSegments(timestamps, transcript, buffer=0.1):
    segmentsToRemove = []
    lastWordEndTime = 0
    
    #sort timestamps by start time
    timestamps.sort(key=lambda x: x["start"])
    
    #remove silences
    for entry in timestamps:
        wordStart = max(0, entry["start"] - buffer)
        wordEnd = entry["end"] + buffer
        
        if lastWordEndTime < wordStart:
            segmentsToRemove.append((lastWordEndTime, wordStart))
        
        lastWordEndTime = wordEnd
    
    #remove filler words
    for entry in timestamps:
        if entry["word"].lower() in fillerWords:  #check if word is filler
            wordStart = max(0, entry["start"] - buffer)
            wordEnd = entry["end"] + buffer
            segmentsToRemove.append((wordStart, wordEnd))
    
    #add segment after last word
    if lastWordEndTime < video_clip.duration:
        segmentsToRemove.append((lastWordEndTime, video_clip.duration))
    
    #detect and remove repetition
    repeatedSegments = detectRepetition(transcript, timestamps)
    segmentsToRemove.extend(repeatedSegments)
    
    #use chatgpt to identify and remove unimportant content
    chatGPTSegmentsToRemove = identifyUnimportantContentChatGPT(transcript, timestamps)
    segmentsToRemove.extend(chatGPTSegmentsToRemove)
    
    return segmentsToRemove

#function to edit video
def editVideo(video_clip, segmentsToRemove):
    segmentsToRemove.sort()
    clipsToKeep = []
    startTime = 0
    for segment in segmentsToRemove:
        segmentStart, segmentEnd = segment
        if startTime < segmentStart:
            clipsToKeep.append(video_clip.subclipped(startTime, segmentStart))
        startTime = segmentEnd
    if startTime < video_clip.duration:
        clipsToKeep.append(video_clip.subclipped(startTime, video_clip.duration))
    finalClip = concatenate_videoclips(clipsToKeep)
    return finalClip

#function to process video
def process_video():
    global video_clip
    videoFilePath = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
    if not videoFilePath:
        return

    #update status
    status_label.config(text="Extracting audio...")
    progress_bar.start()

    #extract audio
    audioFilePath = "temp_audio.wav"
    extractedAudio = extractAudio(videoFilePath, audioFilePath)

    if extractedAudio:
        #transcribe audio
        status_label.config(text="Transcribing audio...")
        transcript, timestamps = transcribeAudio(extractedAudio)

        #identify unimportant segments
        status_label.config(text="Identifying unimportant segments...")
        video_clip = VideoFileClip(videoFilePath)
        segmentsToRemove = identifyOtherUnimportantSegments(timestamps, transcript, buffer=0.1)

        #edit video
        status_label.config(text="Editing video...")
        finalClip = editVideo(video_clip, segmentsToRemove)

        #save edited video
        outputVideoPath = filedialog.asksaveasfilename(title="Save Edited Video", defaultextension=".mp4", filetypes=[("Video Files", "*.mp4")])
        if outputVideoPath:
            finalClip.write_videofile(outputVideoPath, codec="libx264")
            status_label.config(text="Video saved successfully!")
            messagebox.showinfo("Success", f"Edited video saved to: {outputVideoPath}")

    progress_bar.stop()
    status_label.config(text="Ready")

#function to use threading
def startProcessing():
    threading.Thread(target=process_video).start()

#create main window
root = tk.Tk()
root.title("Video Editor")
root.geometry("400x200")

#add button to select and process video
process_button = tk.Button(root, text="Select Video and Edit", command=startProcessing)
process_button.pack(pady=20)

#add progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

#add status label
status_label = tk.Label(root, text="Ready", fg="blue")
status_label.pack(pady=10)

root.mainloop()
