import copy
import glob
import os
from pathlib import Path
import sys
import MainWindow
import startup
import json
from audio_separation import separate_temp

from audio_merging import merge


def get_speakers(models_dir):
    speakers = []
    for _, dirs, _ in os.walk(models_dir):
        for folder in dirs:
            # ... (код для получения информации о модели)
            cur_speaker = {}
            # Ищем G_****.pth
            g = glob.glob(os.path.join(models_dir, folder, 'G_*.pth'))
            if not len(g):
                print("Skipping " + folder + ", no G_*.pth")
                continue
            cur_speaker["model_path"] = g[0]
            cur_speaker["model_folder"] = folder

            # Ищем *.pt (модель кластеризации)
            clst = glob.glob(os.path.join(models_dir, folder, '*.pt'))
            if not len(clst):
                print("Note: No clustering model found for " + folder)
                cur_speaker["cluster_path"] = ""
            else:
                cur_speaker["cluster_path"] = clst[0]

            # Ищем config.json
            cfg = glob.glob(os.path.join(models_dir, folder, '*.json'))
            if not len(cfg):
                print("Skipping " + folder + ", no config json")
                continue
            cur_speaker["cfg_path"] = cfg[0]
            with open(cur_speaker["cfg_path"]) as f:
                try:
                    cfg_json = json.loads(f.read())
                except Exception as e:
                    print("Malformed config json in " + folder)
                for name, i in cfg_json["spk"].items():
                    cur_speaker["name"] = name
                    cur_speaker["id"] = i
                    if not name.startswith('.'):
                        speakers.append(copy.copy(cur_speaker))

    return sorted(speakers, key=lambda x:x["name"].lower())

if __name__ == "__main__":
    try:
        with open("config.json", 'r') as f:
            config_data = json.load(f)              
    except json.JSONDecodeError as e:
        config_data = {}
        with open('config.json', 'w') as f:
            json.dump(config_data, f)
    except FileNotFoundError as e:
        config_data = {}
        with open('config.json', 'w') as f:
            json.dump(config_data, f)
    
    if "initial_setup_done" not in config_data or config_data["initial_setup_done"] == "True":
        startup.initial_setup()
        config_data["initial_setup_done"] = "True"
        with open('config.json', 'w') as f:
            json.dump(config_data, f)
    

    print(Path.cwd())
    input_file = Path(Path.cwd(), "песни", "Цой.mp3")
    temp_path = Path(Path.cwd(), "temp", "Цой")
    temp_vocal_path = Path(temp_path, "vocals.wav")

    speakers = get_speakers(Path(Path.cwd(), "models"))
    
    output_path = Path(Path.cwd(), "output")

    os.chdir("./sovits")
    # from sovits.audio_conversion import convert
    # convert(temp_vocal_path, "0", speakers, "aimodel", "0.0", False, "0.9", temp_path, -40)
    os.chdir("../")

    print(Path.cwd())
    merge(temp_path, temp_path)