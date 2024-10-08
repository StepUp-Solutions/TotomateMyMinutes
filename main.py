"""
main.py

This script automates the process of recording a meeting using OBS (Open Broadcaster Software), transcribing the audio using WhisperX, and generating a meeting minutes prompt based on the transcript.

See README.md for all relevant info

Author: chgayot
Date: 2024-09-14
Version: 1.0
"""

from obswebsocket import obsws, requests
import keyboard
import subprocess
import sys
import time
import threading

import gc
import os
from faster_whisper import WhisperModel#, BatchedInferencePipeline
import torch
import pyperclip

#%%

#Set your OBS websocket password
obs_password = "your_password"
#Choose the transcription model. Recommended: distil-large-v2
model_size = 'distil-medium.en' #"distil-large-v2" #"tiny.en"

#Edit or add your own context and minbute structure
meeting_context = [
    (
        "Weekly Meeting",
        """Write the minutes for the transcript. The speakers are not written down. The transcript was automatic, therefore, there may be mistakes, account for it in your minutes. The context is a tech company, with the minutes from its main meeting. The normal structure for the meeting is as follow, keep it for writing the minutes.
**Title:** Weekly Meeting
**Date and Time:** [Leave Blank if Unknown]
**Location:** [Leave Blank if Unknown]
**Attendees:** [Leave Blank if Unknown]
**Chairperson:** [Leave Blank if Unknown]
**Recorder:** Automated
HR 
Business Devt.
Technical
- Mechanical/Design
- Apps"""
    ),
    (
        "Data Meeting",
        """Write the minutes for the transcript. The speakers are not written down. The transcript was automatic, account for potential mistakes in your minutes. The context is a daily meeting between engineers working on a biomedial signal and data processing. Follow the meeting as per those points: 
**Title:** Weekly Meeting
**Date and Time:** [Leave Blank if Unknown]
**Attendees:** [Leave Blank if Unknown]
What was achieved: 
What was clarified, mentioned or solved during the meeting: 
What's next to be done"""
    ),
    (
    "Project Kickoff Meeting",
    """Write the minutes for the transcript. The speakers are not written down. The transcript was automatic, account for potential mistakes in your minutes. The context is a project kickoff meeting for a new software development project. Follow the meeting as per those points:
    **Title:** Weekly Meeting
    **Date and Time:** [Leave Blank if Unknown]
    **Attendees:** [Leave Blank if Unknown]
    - Project Overview
    - Team Roles and Responsibilities
    - Key Milestones
    - Risks and Mitigation Strategies
    - Next Steps"""
    ),
    (
        "Marketing Strategy Meeting",
        """Write the minutes for the transcript. The speakers are not written down. The transcript was automatic, account for potential mistakes in your minutes. The context is a meeting to discuss the marketing strategy for a new product launch. Follow the meeting as per those points:
    **Title:** Weekly Meeting
    **Date and Time:** [Leave Blank if Unknown]
    **Attendees:** [Leave Blank if Unknown]
    - Market Analysis
    - Target Audience
    - Marketing Channels
    - Budget Allocation
    - Timeline"""
    )
]


#%%

def modify_path_with_cuda():
    """
    Modifies the PATH environment variable to include the CUDA bin directory.

    This function reads the CUDA_PATH environment variable, appends the 'bin/' directory
    to it, and then updates the PATH environment variable to include this new path.
    This is useful for ensuring that CUDA-related executables are available in the system's
    PATH, which is necessary for running CUDA-enabled applications.

    Raises:
        SystemExit: If the CUDA_PATH environment variable is not set.
    """
    # Read the CUDA_PATH environment variable
    cuda_path = os.getenv('CUDA_PATH')
    if not cuda_path:
        print("CUDA_PATH environment variable is not set.")
        sys.exit(1)

    # Append 'bin/' to the CUDA_PATH
    cuda_bin_path = os.path.join(cuda_path, 'bin')

    # Get the current PATH environment variable
    current_path = os.getenv('PATH', '')

    # Append the CUDA bin path to the PATH
    new_path = f"{current_path};{cuda_bin_path}" if os.name == 'nt' else f"{current_path}:{cuda_bin_path}"

    # Set the new PATH environment variable
    os.environ['PATH'] = new_path

    # Print the new PATH for verification
    # print(f"New PATH: {os.getenv('PATH')}")


def launch_obs():
    """
    Launch OBS application by specifying the path to the executable within its installation directory.
    Returns the subprocess.Popen object representing the running process.
    """
    obs_path = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
    try:
        process = subprocess.Popen([obs_path], cwd=r"C:\Program Files\obs-studio\bin\64bit")
        print("OBS has been launched.")
        return process
    except Exception as e:
        print("Failed to launch OBS:", str(e))
        sys.exit(1)

def connect_obs():
    """
    Connect to the OBS Websocket server using the specified host, port, and password.
    Returns the connected OBS client object.
    """
    try:
        client = obsws("localhost", 4455, obs_password)
        client.connect()
        print("Connected to OBS.")
        print(client.call(requests.GetVersion()).getObsVersion())
        return client
    except Exception as e:
        print(f"Could not connect to OBS Websocket: {e}")
        sys.exit(1)
def timer():
    """
    Continuously tracks and prints the elapsed recording time in minutes and seconds.
    This function runs in a loop until the 'recording' flag is set to False.
    """
    start_time = time.time()
    while recording:
        elapsed_time = int(time.time() - start_time)
        minutes, seconds = divmod(elapsed_time, 60)
        print(f"Recording time: {minutes:02}:{seconds:02}", end="\r")
        time.sleep(1)
def start_recording(client):
    """
    Initiates the recording process in OBS using the provided client connection.
    If the recording fails to start, an error message is printed and the program exits.
    """
    try:
        client.call(requests.StartRecord())
        print("Recording started.")
    except Exception as e:
        print("Failed to start recording:", str(e))
        sys.exit(1)


def stop_recording(client):
    """
    Stops the recording in OBS and retrieves the file path where the recording was saved.

    Parameters:
        client (obsws): The WebSocket client connected to OBS.

    Returns:
        str: The path to the recording file or an empty string if not found.

    Raises:
        Exception: An error occurred that prevented stopping the recording or retrieving the path.
    """
    recording_path = ""
    try:
        response = client.call(requests.StopRecord())
        print("Recording stopped.")
        if response.status:  # Check if the response status indicates success
            print(response)
            recording_path = response.datain.get('outputPath', "")
            print(f"Recording saved to: {recording_path}")
        else:
            print("Failed to fetch recording path.")
    except Exception as e:
        print(f"Failed to stop recording: {str(e)}")
        sys.exit(1)
    return recording_path


def close_obs(client):
    """
    Sends a command to OBS to exit cleanly using the WebSocket connection.

    Parameters:
        client (obsws): The WebSocket client connected to OBS.
    """
    try:
        client.call(requests.Exit())
        print("OBS is exiting cleanly.")
    except Exception as e:
        print(f"Failed to send exit command to OBS: {str(e)}")

def transcribe_audio(audio_file, device="cuda", compute_type="float16", batch_size=16):
    """
    Transcribes an audio file using WhisperX, aligns the transcript, and assigns speaker labels.

    Parameters:
        audio_file (str): Path to the audio file to transcribe.
        device (str): The device to run the transcription on, e.g., 'cuda' for GPU.
        compute_type (str): Precision for computation, 'float16' or 'int8'.
        batch_size (int): Batch size for transcription, adjust based on GPU memory.

    Returns:
        A dictionary with transcription results, including speaker labels.
    """

    
    if not os.path.exists(audio_file):
        print("The specified audio file does not exist: ", audio_file)
        return NULL
    else:

        # Initialize the Whisper model with specified settings
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        # batched_model = BatchedInferencePipeline(model=model)
        # Perform transcription
        segments, info = model.transcribe(audio_file,beam_size=5,  condition_on_previous_text=False, vad_filter=True)# batch_size=16)#, 
        print("Starting Transcribing")
        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
        # Transcribe audio

        # Saving the transcription to a file
        output_file_path = audio_file.rsplit('.', 1)[0] + ".txt"

        full_transcript =[]

        # Write the transcription data to the file and calculate speaker times
        with open(output_file_path, 'w') as file:
            for segment in segments:
                # transcript_line = "[%.2fs -> %.2fs] %s\n" % (segment.start, segment.end, segment.text)
                transcript_line = "%s\n" % (segment.text)
                full_transcript.append(transcript_line)
                # print(transcript_line, end='')
                file.write(transcript_line)

        full_transcript ="".join(full_transcript)
        print(full_transcript)
        gc.collect()
        torch.cuda.empty_cache()
        del model
        print("Cleaning Done")
        print(f"Transcription saved to {output_file_path}")
        return output_file_path, full_transcript


def write_prompt(full_transcript):
    """
    Generates a prompt by combining a selected or custom prompt with the provided transcript.

    Parameters:
        full_transcript (str): The full transcript of the audio file.

    Returns:
        str: The combined prompt with the transcript.
    """

    # Prompt user to select a prompt number or enter '0' for custom
    print("Select a prompt number or enter '0' for a custom prompt:")
    for index, (name, desc) in enumerate(meeting_context, start=1):
        print(f"{index}. {name}")  # Display the name for easy identification

    selection = input("Your choice: ")
    if selection == '0':
        custom_prompt = input("Enter your custom prompt: ")
        selected_prompt = custom_prompt
    elif selection.isdigit() and 1 <= int(selection) <= len(meeting_context):
        selected_prompt = meeting_context[int(selection) - 1][1]  # Select the corresponding prompt text
    else:
        print("Invalid selection. Using default prompt.")
        selected_prompt = meeting_context[0][1]  # Use the first prompt as a default

    # Combine the selected or custom prompt with the transcript
    prompt_full = selected_prompt + "\n\nSTART OF TRANSCRIPT:\n" + full_transcript
    return prompt_full

    
def main():
    global recording
    recording = True

    print("Welcome to TotomateMyMinutes")
    modify_path_with_cuda()
    
    # For testing on a previously recorded file

    #data = transcribe_audio(r"C:/_Videos/2024-06-07 14-43-51.mkv")
    #transcript_path, full_transcript = data
    #print(transcript_path)
   # print(full_transcript)
    #prompt = write_prompt(full_transcript)
    #print(prompt)
    # Copy the full prompt to the clipboard
   # pyperclip.copy(prompt)
   # print("Prompt has been copied to the clipboard.")
    
   # input("")
    
    obs_process = launch_obs()
    time.sleep(13)  # Allow OBS to launch completely
    client = connect_obs()
    start_recording(client)

    timer_thread = threading.Thread(target=timer)
    timer_thread.start()

    print("Press Enter to stop recording...")
    input("")
    recording = False
    timer_thread.join()

    recording_path = stop_recording(client)
    # close_obs(client) #Not supported at the moment
    client.disconnect()

    print("Disconnected from OBS and exiting.")
    transcript_path, full_transcript = transcribe_audio(recording_path)
    prompt = write_prompt(full_transcript)
    print(prompt)
    # Copy the full prompt to the clipboard
    pyperclip.copy(prompt)
    print("Prompt has been copied to the clipboard.")

    


if __name__ == "__main__":
    main()
