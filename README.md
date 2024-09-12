# Fully Open Source Note and Minute Taking for Online or On-Site Meetings

**No more crying for having to take the minutes!**

![You at the last meeting](img/cry.jpg)
## Overview

This project is your ultimate meeting minute generator for effortlessly taking notes and minutes during online or on-site meetings. No API keys required—just use your own chat AI! Whether you're a Windows or Linux, this tool has got you covered.

## Usage

1. **Run the Script:**
   - On **Windows**: Execute `totomate.bat`.
   - On **Linux**: Execute `totomate.sh` (Untested, but let's be optimistic!).

2. **End the Meeting:**
   - Press `Enter` when the meeting concludes.

3. **Transcribe and Contextualize:**
   - Once transcribed, select the context of the meeting.
   - Paste (`Ctrl+V`) the content of the clipboard into ChatGPT, [Open WebUI](https://github.com/open-webui/open-webui), or your favorite chat AI (ChatGPT 4o or better recommended).

## Settings

### Model for Transcribing
- **Examples:** `tiny.en`, `medium`, `distil-large-v2`, `faster-distil-medium.en`, `large-v3`,... check distil- and Whisper model for a full list.

### Context for Different Meetings
- Customize the context to fit various meeting types.

## Principle

1. **OBS Records All Sounds:**
   - OBS captures audio from both the microphone and the computer.
   - The recording is transcribed using Faster-Whisper.
   - Both the audio and transcriptions are stored in OBS's default folder—typically your default Video folder.

2. **Contextual Transcription:**
   - A context is added to the transcript to structure the minutes as expected.
   - The full prompt is copied to the clipboard for easy pasting into your AI tool.

## Setup

### Clone the Repository
- Clone the repository (unexpected, right?).

### Open a Terminal
- Navigate to the cloned repository.

### (Optional) Create a Virtual Environment
- Run `python -m venv .venv` to create a virtual environment.
- **Activate the Virtual Environment:**
  - On **Windows**: Run `.\.venv\Scripts\activate`.
  - On **Linux/Mac**: Run `source .venv/bin/activate`.

### Install Faster-Whisper
- Follow the instructions on [Faster-Whisper GitHub](https://github.com/SYSTRAN/faster-whisper) to install it.
- **(Windows) Update PATH Environment Variables:**
  - Open Environment Variables for the system.
  - Edit the `PATH` variable.
  - You should see an entry like `C:\Program Files\NVIDIA\CUDNN\vx.x\bin`.
  - Copy this entry and add another one with the updated version, e.g., `C:\Program Files\NVIDIA\CUDNN\vx.x\bin\12.x`, where `12.x` is the version you just installed. You can open the folder to verify the correct version.
  - Reboot your system (or refresh your PATH environment variables).

### Python Compatibility
- Should be compatible with Python 3.8+.
- (Create a virtual environment if you prefer.)

### Configure OBS
1. **Launch OBS:**
   - On the bottom right, click `Settings`.

2. **Change the Following Parameters:**
   - **Save OBS Recording as mp3** (Optional, but recommended—your computer will thank you).
   - In the `Output` tab:
     - Select `Output Mode`: `Advanced`.
     - Go to `Recording`.
     - Select `Type`: `Custom Output (Ffmpeg)`.
     - `Container format`: `mp3`.
     - `Video Encoder`: `Disable Encoder`.

![OBS Config 1](img/obs1.png)

3. **Add Audio Sources:**
   - In `Sources`, press `+` and add:
     - `Audio Input Capture` - Leave on Default.
     - `Audio Output Capture` - Same.

![OBS Config 2](img/obs2.png)

### Install Dependencies
- Run `pip install -r requirements.txt`.

### (Optional) Create a shortcut
    - (Windows) Right-click on the script "Send To" -> "Desktop (create shortcut)"

**Done!** You're all set to take notes like a pro.

---

**Note:** This documentation is fully open source, just like the code. Feel free to contribute, improve, or even add more jokes!

**Maintained by @chgayot at StepUp Solutions**