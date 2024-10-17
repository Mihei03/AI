from pydub import AudioSegment
from pathlib import Path

def merge(folder_path, result_path, result_filename = "output"):
    tracks = []
    for f in folder_path.glob("*.wav"):
        if f.name != "vocals.wav":
            segment = AudioSegment.from_file(f.absolute(), format="wav")
            tracks.append(segment)

    if len(tracks) == 0:
        return
        
    overlayed_output = tracks[0]
    for i in range(1, len(tracks)):
        overlayed_output = overlayed_output.overlay(tracks[i], position=0)

    combined_file_name = result_path / f"{result_filename}.wav"
    overlayed_output.export(combined_file_name, format="wav")