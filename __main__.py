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

class PathManager:
    def __init__(self):
        # Get the AI_code directory path
        self.ai_code_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        # Ensure we're in the AI_code directory
        os.chdir(self.ai_code_dir)
        
    def get_path(self, *parts):
        """Create paths relative to AI_code directory"""
        return Path(self.ai_code_dir, *parts)

def get_speakers(models_dir):
    speakers = []
    for _, dirs, _ in os.walk(models_dir):
        for folder in dirs:
            cur_speaker = {}
            # Look for G_****.pth
            g = glob.glob(os.path.join(models_dir, folder, 'G_*.pth'))
            if not len(g):
                print("Skipping " + folder + ", no G_*.pth")
                continue
            cur_speaker["model_path"] = g[0]
            cur_speaker["model_folder"] = folder

            # Look for *.pt (clustering model)
            clst = glob.glob(os.path.join(models_dir, folder, '*.pt'))
            if not len(clst):
                print("Note: No clustering model found for " + folder)
                cur_speaker["cluster_path"] = ""
            else:
                cur_speaker["cluster_path"] = clst[0]

            # Look for config.json
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
    # Initialize path manager
    path_mgr = PathManager()
    
    # Ensure required directories exist
    required_dirs = ['песни', 'temp', 'models', 'output', 'sovits']
    for dir_name in required_dirs:
        dir_path = path_mgr.get_path(dir_name)
        dir_path.mkdir(exist_ok=True)
    
    # Handle config.json
    config_path = path_mgr.get_path('config.json')
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)              
    except (json.JSONDecodeError, FileNotFoundError):
        config_data = {}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
    
    if "initial_setup_done" not in config_data or config_data["initial_setup_done"] == "True":
        startup.initial_setup()
        config_data["initial_setup_done"] = "True"
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

    # Set up paths for processing
    input_file = path_mgr.get_path("песни", "duhast.mp3")
    temp_path = path_mgr.get_path("temp", "duhast")
    temp_vocal_path = Path(temp_path, "vocals.wav")
    
    # Create temp directory if it doesn't exist
    temp_path.mkdir(parents=True, exist_ok=True)

    # Get speakers and set output path
    speakers = get_speakers(path_mgr.get_path("models"))
    output_path = path_mgr.get_path("output")

    # Process audio
    separate_temp(2, input_file)

    # Change to sovits directory for conversion
    sovits_path = path_mgr.get_path("sovits")
    os.chdir(sovits_path)
    from audio_conversion import convert
    convert(temp_vocal_path, "0", speakers, "aimodel", "0.0", False, "0.9", temp_path, -40)
    
    # Return to AI_code directory
    os.chdir(path_mgr.ai_code_dir)

    # Merge the processed audio
    merge(temp_path, temp_path)
