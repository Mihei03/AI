from pathlib import Path
import subprocess
from pydub import AudioSegment

def split_audio(audio_path, output_directory):
    audio = AudioSegment.from_file(audio_path)
    fragment_length_ms = 15 * 1000
    fragments = []
    for i in range(0, len(audio), fragment_length_ms):
        fragment = audio[i:i+fragment_length_ms]
        fragments.append(fragment)

    Path.mkdir(output_directory, exist_ok=True)
    for i, fragment in enumerate(fragments):
        vocal_part_path = output_directory / f"{i:08}.wav"
        fragment.export(vocal_part_path, format="wav")


def separate(track_count, audio_path, output_directory):
    command = f"spleeter separate -p spleeter:{track_count}stems {audio_path} -o {output_directory}"
    subprocess.call(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def separate_temp(track_count, audio_path):
    temp_path = Path.cwd() / "temp"
    Path.mkdir(temp_path, exist_ok=True)

    separate(track_count, audio_path, temp_path)