# Cut-Eye: An AI Video Editor

I’d like to thank everyone who contributed to the success of this project. I am specifically
grateful to my project supervisor, Vivek Singh, for his invaluable feedback and guidance
throughout the development of this project. I also want to extend my thanks to the School of
Engineering, Computing, and Mathematics, as well as the University of Plymouth as a whole
, for providing me with the resources and facilities I required, as well as an education that
helped me gain perspective on various features of my project. Finally, I am thankful to all
my friends and family, who supported me emotionally through this journey. Without their
support, this project would have simply been impossible.

## About this project:

The industry of video content creation is continually growing; however, the process of manual
editing is still time-consuming. The removal of unimportant content is a stage of video editing
that requires little skill yet can take a long time. This project develops an AI-powered video
editor to automate these tasks, making use of speech-to-text and natural language processing
(NLP). The program uses OpenAI’s Whisper for transcription, ChatGPT for unimportant content
detection, and MoviePy for editing. Tkinter is also used to create an intuitive user interface.
Testing of the program showed an 88% reduction in the number of filler words, and 5x to 10x
faster processing speeds compared to manual editing. This program reduces the skill barrier
required for video editing, allowing more people to create professional-looking videos. It also
increases the efficiency of the video editing process, allowing editors to focus their skills on
creative endeavours.

This project’s main objective is to automate any task that is both time consuming and requires
little skill. This includes the removal of silence, filler words, and repetition, as well as the slightly
more complex task of removing other unimportant content, like tangents. Whilst doing this, it’s
important that the natural flow of the video is not disturbed. This means over-cutting should be
avoided. The ideal scenario is that someone could watch a video that was edited by my program
without noticing anything. I want the design of the program to be user-friendly. There should be
a graphical interface that is designed so any user can understand how the program is meant to
be used. The aesthetics of the interface is not as important as its usability. Finally, my last
objective will be to make sure the program is more efficient than manual editing. If you gave the
same footage to a manual editor and my program, the program should edit it significantly faster.

The features, general user base, and accepted input file types of the project are all in-scope. The
program will accept MP4 files. Other file types should be accepted but MP4 files are a necessity.
These videos should include spoken content and avoid music and sound effects for the best
results. The features that will be added to my program will include filler word removal, repetition
removal, silence removal, and the removal of any other unimportant content. The intended user
base of this program is content creators and any companies that are looking to create online
media. However, students using this program to make their revision more efficient was also
considered during the scope generation process. Visual editing has always been outside the
scope of this project. This means scene transitions, colour correction and VFX were never
considered as potential features the program could include. This is because visual editing
requires more creativity and therefore can’t as easily be automated. The integration of this
program into popular editing programs was marked down as potentially in scope, but only if the
project went faster than anticipated

## Demo Video:
https://youtu.be/e_6sUDib4l0?si=vz8JxxtmvB5Zkoc0

## Installation Instructions

1.	Install Python and FFmpeg
2.	Install all code libraries listed in requirements.txt
3.	Download these two images<img width="1000" height="1000" alt="logo" src="https://github.com/user-attachments/assets/c376b678-6974-41aa-8e55-c8aeed24bf57" /><img width="242" height="73" alt="name" src="https://github.com/user-attachments/assets/73cfe291-0c9f-432d-abfc-c6431796f477" />


5.	place those images into a new folder
6.	Replace the file directory on line 381 of AudioToTextGPT.py with the file directory of the pics folder
a.	Tip: use “//” instead of “\”
7.	Replace the file directory on line 397 of AudioToTextGPT.py with the file directory of the pics folder



if my program explodes your computer, sorry
