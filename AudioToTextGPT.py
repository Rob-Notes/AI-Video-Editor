import tkinter as tk
from tkinter import filedialog, messagebox, ttk, PhotoImage, simpledialog
from moviepy import VideoFileClip, concatenate_videoclips
import whisper
import threading
from openai import OpenAI
from PIL import Image, ImageTk
import os
import subprocess
import spacy

#initialise whisper model
os.environ["WHISPER_PROGRESS"] = "0"
whisperModel = whisper.load_model("base")

#filler word list
fillerWords = ["um", "uh", "like", "you know", "actually", "basically", "seriously", "literally"]

nlp = spacy.load("en_core_web_sm")

#initialise openai client
openAIClient = OpenAI(api_key="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")  

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

def isFiller(word, transcript):
    doc = nlp(transcript)
    for token in doc:
        if token.text.lower() == word.lower():
            if token.pos_ == "INTJ" or (token.i > 0 and doc[token.i-1].text in {",", "...", "—"}):
                return True
    return False

#function to identify unimportant segments using chatgpt
def identifyUnimportantContentChatGPT(transcript, timestamps, maxTokens=15000):
    
    def splitTranscript(text, tokenLimit):
        words = text.split()
        chunks = []
        currentChunk = []
        currentCount = 0
        
        for word in words:
            wordTokens = len(word) + 1 
            if currentCount + wordTokens <= tokenLimit:
                currentChunk.append(word)
                currentCount += wordTokens
            else:
                chunks.append(" ".join(currentChunk))
                currentChunk = [word]
                currentCount = wordTokens
        
        if currentChunk:
            chunks.append(" ".join(currentChunk))
        return chunks
    
    allSegments = []
    chunks = splitTranscript(transcript, maxTokens)
    
    for chunk in chunks:
        #prepare prompt
        prompt = f"""
        Below is a transcript of a video. Identify the timestamps of any unimportant content (e.g., tangents, off-topic discussions, paraphrased repetitions) that should be removed. 
        Return the timestamps in the format: [(start1, end1), (start2, end2), ...].

        Transcript:
        {chunk}

        Timestamps:
        {timestamps}

        Return only the timestamps of unimportant content. Do not rephrase or summarize the transcript.
        """

        try:
                response = openAIClient.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                )
            
                output = response.choices[0].message.content.strip()
            
                #safely evaluate response
                if output.startswith("[(") and output.endswith(")]"):
                    segments = eval(output)
                    if all(isinstance(x, tuple) and len(x) == 2 for x in segments):
                        allSegments.extend(segments)
                    
        except Exception as e:
            print(f"Error processing chunk: {str(e)}")
            continue

    if allSegments:
        allSegments.sort()
        merged = [allSegments[0]]
        for current in allSegments[1:]:
            last = merged[-1]
            if current[0] <= last[1]:  
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)
        return merged
    
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
        word = entry["word"].lower()
        if word in fillerWords:  #check if word is filler
            if isFiller(word, transcript):
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

def preprocessVideo(inputPath, outputFolder="temp"):
    if compressionSettings["no_compression"]:
        return inputPath 
    
    os.makedirs(outputFolder, exist_ok=True)
    outputPath = os.path.join(outputFolder, "compressed.mp4")
    
    ffmpegCMD = [
        "ffmpeg",
        "-i", inputPath,
        "-vf", f"scale={compressionSettings['width']}:-2",
        "-r", str(compressionSettings['fps']),
        "-c:v", "libx264",
        "-preset", compressionSettings["preset"],
        "-crf", str(compressionSettings['crf']),
        "-c:a", "aac",
        "-b:a", "64k",
        "-y",
        "-loglevel", "error",
        outputPath
    ]
    
    try:
        subprocess.run(ffmpegCMD, check=True)
        return outputPath
    except subprocess.CalledProcessError as e:
        messagebox.showerror("FFmpeg Error", f"Failed to compress video: {e}")
        return None
    
#function to process video
def processVideo():
    global video_clip
    videoFilePath = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
    if not videoFilePath:
        return

    try:
        #setup progress
        progressBar["value"] = 0
        root.update_idletasks()

        #compress video
        statusLabel.config(text="Compressing video...")
        progressBar["value"] = 20
        if compressionSettings["no_compression"]:
            compressedPath = videoFilePath
        else:
            compressedPath = preprocessVideo(videoFilePath)
        
        if not compressedPath:
            return
        
        #load compressed video
        statusLabel.config(text="Loading video...")
        progressBar["value"] = 30
        video_clip = VideoFileClip(compressedPath)

        #extract audio
        statusLabel.config(text="Extracting audio...")
        progressBar["value"] = 40
        audioFilePath = "temp_audio.wav"
        if not extractAudio(compressedPath, audioFilePath):
            return

        #transcribe
        statusLabel.config(text="Transcribing audio...")
        progressBar["value"] = 50
        transcript, timestamps = transcribeAudio(audioFilePath)

        #process video
        statusLabel.config(text="Identifying segments...")
        progressBar["value"] = 70
        segmentsToRemove = identifyOtherUnimportantSegments(timestamps, transcript, buffer=0.1)

        statusLabel.config(text="Editing video...")
        progressBar["value"] = 80
        finalClip = editVideo(video_clip, segmentsToRemove)

        #save
        statusLabel.config(text="Saving video...")
        progressBar["value"] = 90
        outputVideoPath = filedialog.asksaveasfilename(
            title="Save Edited Video",
            defaultextension=".mp4",
            filetypes=[("Video Files", "*.mp4")]
        )
        if outputVideoPath:
            finalClip.write_videofile(
                outputVideoPath,
                codec="libx264",
                audio_codec="aac",
                threads=4 
            )
            statusLabel.config(text="Video saved successfully!")
            messagebox.showinfo("Success", f"Edited video saved to: {outputVideoPath}")

    except Exception as e:
        messagebox.showerror("Error", f"Processing failed: {str(e)}")
    finally:
        #cleanup temporary files
        temp_files = [audioFilePath]
        if not compressionSettings["no_compression"]:
            temp_files.append(compressedPath)

        for file in temp_files:
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass
        
        progressBar["value"] = 100
        statusLabel.config(text="Ready")
        root.update_idletasks()

#function to use threading
def startProcessing():
    threading.Thread(target=processVideo).start()

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tipwindow, text=self.text, bg="#ffffe0", 
                        relief=tk.SOLID, borderwidth=1, padx=5, pady=5)
        label.pack()

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()

def openSettings():
    settingsWindow = tk.Toplevel(root)
    settingsWindow.title("Compression Settings")
    settingsWindow.geometry("400x400")
    settingsWindow.resizable(False, False)
    
    #main frame
    main_frame = tk.Frame(settingsWindow, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    #no compression checkbox
    noCompVar = tk.IntVar(value=1 if compressionSettings["no_compression"] else 0)
    no_comp_check = tk.Checkbutton(main_frame, text="No Compression (use original video)", 
                                 variable=noCompVar, onvalue=1, offvalue=0)
    no_comp_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))
    ToolTip(no_comp_check, "When checked, the original video will be used without any compression")

    #resolution
    tk.Label(main_frame, text="Resolution Width (px):").grid(row=1, column=0, sticky="w", pady=(0,5))
    resVar = tk.StringVar(value=str(compressionSettings["width"]))
    res_entry = tk.Entry(main_frame, textvariable=resVar)
    res_entry.grid(row=1, column=1, sticky="ew", pady=(0,5))
    ToolTip(res_entry, "Recommended: 480-1280 (lower=faster processing)")

    #frame rate
    tk.Label(main_frame, text="Frame Rate (FPS):").grid(row=2, column=0, sticky="w", pady=(0,5))
    fpsVar = tk.StringVar(value=str(compressionSettings["fps"]))
    fps_entry = tk.Entry(main_frame, textvariable=fpsVar)
    fps_entry.grid(row=2, column=1, sticky="ew", pady=(0,5))
    ToolTip(fps_entry, "Recommended: 15-30 (lower=faster processing)")

    #compression Level
    tk.Label(main_frame, text="Compression Quality:").grid(row=3, column=0, sticky="w", pady=(0,5))
    crfVar = tk.IntVar(value=compressionSettings["crf"])
    crf_scale = tk.Scale(main_frame, from_=0, to=51, orient=tk.HORIZONTAL, variable=crfVar,
                       showvalue=1)
    crf_scale.grid(row=3, column=1, sticky="ew", pady=(0,5))
    tk.Label(main_frame, text="0=lossless, 23=high, 28=medium, 51=lowest").grid(
        row=4, column=1, sticky="w", pady=(0,10))

    #preset
    tk.Label(main_frame, text="Encoding Speed:").grid(row=5, column=0, sticky="w", pady=(0,5))
    presetVar = tk.StringVar(value=compressionSettings["preset"])
    preset_menu = tk.OptionMenu(main_frame, presetVar, 
                              "ultrafast", "superfast", "veryfast", 
                              "faster", "fast", "medium")
    preset_menu.grid(row=5, column=1, sticky="ew", pady=(0,10))
    ToolTip(preset_menu, "Faster encoding = larger files")

    def toggleCompression():
        state = "disabled" if noCompVar.get() == 1 else "normal"
        res_entry.config(state=state)
        fps_entry.config(state=state)
        crf_scale.config(state=state)
    
        if state == "disabled":
            preset_menu.config(state="disabled")
        else:
            preset_menu.config(state="normal")

    #bind checkbox to toggle function
    no_comp_check.config(command=toggleCompression)
    
    toggleCompression()

    #button frame
    btn_frame = tk.Frame(main_frame)
    btn_frame.grid(row=6, column=0, columnspan=2, pady=(10,0))

    def saveSettings():
        try:
            # Save settings
            compressionSettings.update({
                "width": int(resVar.get()),
                "fps": int(fpsVar.get()),
                "crf": int(crfVar.get()),
                "preset": presetVar.get(),
                "no_compression": bool(noCompVar.get()) 
            })
            settingsWindow.destroy()
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Invalid Settings", f"Please check your values:\n{str(e)}")

    tk.Button(btn_frame, text="Save", command=saveSettings, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Reset", command=lambda: [
        noCompVar.set(0),
        resVar.set("640"), 
        fpsVar.set("15"), 
        crfVar.set(28), 
        presetVar.set("fast"),
        toggleCompression()
    ], width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cancel", command=settingsWindow.destroy, width=10).pack(side=tk.LEFT, padx=5)

    #make columns resizable
    main_frame.columnconfigure(1, weight=1)

#create main window
root = tk.Tk()
root.title("Video Editor")
root.geometry("1280x720")
root.configure(bg="#96adc8")

compressionSettings = {
    "width": 640,
    "fps": 15,
    "crf": 28,
    "preset": "fast",
    "no_compression": False 
}

#add logo
try:
    logoImage = Image.open("D://final_project//pics//logo.png")
    logoImage = logoImage.resize((100, 100), Image.LANCZOS)
    logo = ImageTk.PhotoImage(logoImage)

    logoLabel = tk.Label(root, image=logo, bg="#96adc8")
    logoLabel.place(x=10, y=10)
except Exception as e:
    print(f"Error loading logo: {e}")
    

#create centre frame
centerFrame = tk.Frame(root, bg="#96adc8")
centerFrame.pack(pady=(100, 0))

#add name image
try:
    nameImage = Image.open("D://final_project//pics//name.png")
    nameImage = nameImage.resize((300, 100), Image.LANCZOS)
    namePhoto = ImageTk.PhotoImage(nameImage)
    
    name_label = tk.Label(centerFrame, image=namePhoto, bg="#96adc8")
    name_label.image = namePhoto
    name_label.pack(pady=(0, 10))
except Exception as e:
    print(f"Error loading name image: {e}")

#add subtitle
subtitle = tk.Label(centerFrame, 
                   text="Professional Video Editor", 
                   bg="#96adc8", 
                   fg="#05154e",
                   font=("Arial", 12, "italic"))
subtitle.pack()


#frame for both buttons
button_frame = tk.Frame(root, bg="#96adc8")
button_frame.pack(pady=20)

#process button
processButton = tk.Button(
    button_frame, 
    text="Select Video and Edit", 
    command=startProcessing, 
    bg="#00a676",
    padx=15,
    pady=5
)
processButton.pack(side=tk.LEFT, padx=(0, 10))

#settings button
settingsButton = tk.Button(
    button_frame, 
    text="Settings", 
    command=openSettings,
    bg="#f0f0f0",
    padx=15,
    pady=5
)
settingsButton.pack(side=tk.LEFT)

#add progress bar
progressBar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progressBar.pack(pady=10)

#add status label
statusLabel = tk.Label(root, text="Ready", bg="#96adc8", fg="#05154e")
statusLabel.pack(pady=10)

root.mainloop()
