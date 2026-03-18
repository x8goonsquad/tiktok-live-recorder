import os
from datetime import datetime
import subprocess

def create_output_folder(username):
    folder = os.path.join("recordings", username)
    os.makedirs(folder, exist_ok=True)
    return folder

def merge_ts_segments(output_folder, username):
    segments_file = os.path.join(output_folder, "segments.txt")
    final_file = os.path.join(output_folder, f"{username}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}_final.mp4")

    if not os.path.exists(segments_file):
        return

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-f", "concat",
        "-safe", "0",
        "-i", segments_file,
        "-c", "copy",
        final_file
    ]
    subprocess.run(cmd)