# helpers.py
import os
import sys
import datetime
import signal

def log(message):
    """Skriver ut meddelanden med timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[*] {timestamp} - {message}")

def create_output_folder(username):
    """Skapar inspelningsmapp om den inte finns"""
    folder = os.path.join("recordings", username)
    os.makedirs(folder, exist_ok=True)
    return folder

def stop_recording(signal_received=None, frame=None):
    """Stoppar inspelning vid Ctrl+C"""
    log("KeyboardInterrupt received, stopping recording...")
    sys.exit(0)