import glob
import os
from pathlib import Path
import shutil
import subprocess
import MainWindow
import startup
import json
from audio_separation import separate_temp
from audio_separation import split_audio
from audio_merging import merge
import soundfile
import librosa


def get_speakers(models_dir):
    speakers = []
    
    for _, directories, _ in os.walk(models_dir):
        for folder in directories:
            current_speaker = {}
            current_path = Path(models_dir, folder)
    
            # Ищем G_****.pth
            pth_path_template = str(current_path / "G_*.pth")
            pth_paths = glob.glob(pth_path_template)
            if len(pth_paths) == 0:
                print(f"Skipping {folder} no G_*.pth")
                continue

            current_speaker["model_path"] = pth_paths[0]
            current_speaker["model_folder"] = folder

            # Ищем *.pt (модель кластеризации)
            pt_path_template = str(current_path / "*.pt")
            cluster_models = glob.glob(pt_path_template)
            if len(cluster_models) == 0:
                print(f"Note: No clustering model found for {folder}")
                current_speaker["cluster_path"] = ""
            else:
                current_speaker["cluster_path"] = cluster_models[0]

            # Ищем config.json
            json_path_template = str(current_path / "*.json")
            configs = glob.glob(json_path_template)
            if len(configs) == 0:
                print(f"Skipping {folder}, no config json")
                continue

            current_speaker["cfg_path"] = configs[0]
            with open(current_speaker["cfg_path"]) as f:
                try:
                    cfg_json = json.loads(f.read())
                except Exception as e:
                    print("Malformed config json in " + folder)
                for name, i in cfg_json["spk"].items():
                    current_speaker["name"] = name
                    current_speaker["id"] = i
                    if not name.startswith('.'):
                        speakers.append(current_speaker)

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
    
    if "initial_setup_done" not in config_data or config_data["initial_setup_done"] != "True":
        try:
            startup.initial_setup()
            config_data["initial_setup_done"] = "True"
            with open('config.json', 'w') as f:
                json.dump(config_data, f)
        except Exception as e:
            print("an error occured while running startup")
            print(e)
            exit()


    # MainWindow.show()

    if Path.exists(Path.cwd() / "temp"):
        shutil.rmtree(Path.cwd() / "temp")

    Path.mkdir(Path.cwd() / "temp", exist_ok=True)

    folder_path = str(Path.cwd() / "песни" / "*.mp3")
    print("Песни:")
    files = glob.glob(folder_path)
    for file in files:
        print(file.split('\\')[-1])

    name = input("song name in песни folder with extension => ")
    if not name: 
        print("name cannot be empty")
        exit()

    input_file = Path.cwd() / "песни" / name
    if not Path.exists(input_file):
        print(f"{input_file} doesn't exists")
        exit()
    
    if not Path.is_file(input_file):
        print(f"{input_file} is not a file")
        exit()
    
    models_path = Path.cwd() / "models"
    temp_path = Path.cwd() / "temp" / name[:-4]
    temp_raw_path = temp_path / "raw"

    speakers = get_speakers(models_path)

    for i in range(0, len(speakers)):
        print(f"[{i}]", speakers[i]["name"])

    speaker_select = int(input("speaker id => "))
    if speaker_select < 0 or speaker_select >= len(speakers):
        print("invalid input")
        exit()
    
    output_path = Path.cwd() / "output"

    separate_temp(2, input_file)
    split_audio(temp_path / "vocals.wav", temp_raw_path)
    

    os.chdir("./sovits")
    from sovits.audio_conversion import convert
    convert(temp_raw_path, temp_path, speakers[0], noise_scale=0.9)
    os.chdir("../")

    merge(temp_path, temp_path)