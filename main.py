from obswebsocket import obsws, requests
import keyboard
import subprocess
import sys
import time
import threading
import whisperx
import gc
import os
from pyannote.audio import Pipeline
import torch

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
    try:
        client = obsws("localhost", 4455, "AXoKSDc4X2k57wQc")
        client.connect()
        print("Connected to OBS.")
        print(client.call(requests.GetVersion()).getObsVersion())
        return client
    except Exception as e:
        print(f"Could not connect to OBS Websocket: {e}")
        sys.exit(1)

def timer():
    start_time = time.time()
    while recording:
        elapsed_time = int(time.time() - start_time)
        minutes, seconds = divmod(elapsed_time, 60)
        print(f"Recording time: {minutes:02}:{seconds:02}", end="\r")
        time.sleep(1)

def start_recording(client):
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
        # Load the Whisper model
        # model = whisperx.load_model("distil-large-v2", device, compute_type=compute_type)
        model = whisperx.load_model("tiny.en", device, compute_type=compute_type)
        # Load audio
        audio = whisperx.load_audio(audio_file)
        print("Starting Transcribing")
        # Transcribe audio
        result = model.transcribe(audio, batch_size=batch_size)
        print(result["segments"])  # Print segments before alignment

        # Clean up model if needed
        # delete model if low on GPU resources
        gc.collect()
        torch.cuda.empty_cache()
        del model
        print("Cleaning Done")
        # # Load alignment model
        # model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)

        # # Align output
        # result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
        # print(result["segments"])  # Print segments after alignment

        # Clean up alignment model if needed

        # gc.collect()
        # torch.cuda.empty_cache()
        # del model_a

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token="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")

        # send pipeline to GPU (when available)
        # pipeline.to(torch.device("cuda"))

        from pyannote.audio.pipelines.utils.hook import ProgressHook
        with ProgressHook() as hook:
            diarization = pipeline(audio_file, hook=hook, min_speakers=2, max_speakers=5)

        # print the result
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
        # Perform diarization
        # diarize_model = whisperx.DiarizationPipeline(use_auth_token="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", device=device)

        # # Assign speaker labels
        # diarize_segments = diarize_model(audio)
        # result = whisperx.assign_word_speakers(diarize_segments, result)
        # print(diarize_segments)
        # print(result["segments"])  # Print segments with assigned speaker IDs

        # Saving the transcription to a file
        output_file_path = audio_file.rsplit('.', 1)[0] + ".txt"
    # Dictionary to hold total speaking time for each speaker
        speaker_times = {}

        # Write the transcription data to the file and calculate speaker times
        with open(output_file_path, 'w') as file:
            for segment in result["segments"]:
                speaker = segment.get("speaker", "Unknown")
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                duration = end - start

                # Update the total speaking time for the speaker
                if speaker in speaker_times:
                    speaker_times[speaker] += duration
                else:
                    speaker_times[speaker] = duration

                # Write the segment to the file
                line = f"[Speaker {speaker}: {start:.2f}s -> {end:.2f}s] {text}\n"
                file.write(line)

            # Append the total speaking times for each speaker at the end of the file
            file.write("\nSpeaker Summary:\n")
            for speaker, total_time in speaker_times.items():
                file.write(f"{speaker}: {total_time:.2f} seconds\n")
        
        print(f"Transcription saved to {output_file_path}")
        return output_file_path


    
def main():
    global recording
    recording = True

    transcribe_audio(r"C:/_Videos/2024-04-29 10-18-11.mp3")
    
    input("")
    
    obs_process = launch_obs()
    time.sleep(10)  # Allow OBS to launch completely
    client = connect_obs()
    start_recording(client)

    timer_thread = threading.Thread(target=timer)
    timer_thread.start()

    print("Press Enter to stop recording...")
    input("")
    recording = False
    timer_thread.join()

    recording_path = stop_recording(client)
    client.disconnect()
    close_obs(client)
    print("Disconnected from OBS and exiting.")
    transcript_path = transcribe_audio(recording_path)


if __name__ == "__main__":
    main()
