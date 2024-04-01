from pathlib import Path
import subprocess

def separate(track_count, audio_path, output_path):
    command = f"spleeter separate -p spleeter:{track_count}stems {audio_path} -o {output_path}"
    process = subprocess.call(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def separate_temp(track_count, audio_path):
    temp_path = Path(Path.cwd(), "temp")
    Path.mkdir(temp_path, exist_ok=True)

    separate(track_count, audio_path, temp_path)