import json
import shutil
from git import Repo
from pathlib import Path
from git import RemoteProgress
from tqdm import tqdm
import model_loader
import extraction

SOVITS_DIR = Path(Path.cwd(), "sovits")
MODELS_DIR = Path(Path.cwd(), "models")

def _load_sovits():
    sovits_url = "https://github.com/effusiveperiscope/so-vits-svc/archive/refs/heads/eff-4.0.zip"
    sovits_download = str(Path(Path.cwd(), "sovitsarch.zip"))
    model_loader.download([sovits_url], filenames=[sovits_download])

    extraction.extract(sovits_download, "./")
    
    Path.rename(Path("so-vits-svc-eff-4.0"), "sovits")

    converter_path = Path(Path.cwd(), "audio_conversion.py")
    shutil.copy(converter_path, SOVITS_DIR)

    print("so-vits-svc cloned")


def _load_hubert_model():
    model_loader.download(["https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/checkpoint_best_legacy_500.pt"],
              filenames=[f"{SOVITS_DIR}/hubert/checkpoint_best_legacy_500.pt"])
    

def _load_kanye_model():
    if not Path.exists(MODELS_DIR):
        Path.mkdir(MODELS_DIR)

    downloaded_filename = Path(MODELS_DIR, "kanye.zip")
    model_loader.download(["https://mega.nz/file/Dr40kCQI#G3bEWPvUvTa9SBJKQt7rETgcFds4ssnJF0nGN9aAXTk"], filenames=[downloaded_filename])
    extraction.extract(downloaded_filename, MODELS_DIR)


def initial_setup():
    _load_sovits()
    _load_hubert_model()
    _load_kanye_model()