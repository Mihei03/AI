import shutil
from git import Repo
from pathlib import Path
from git import RemoteProgress
from tqdm import tqdm
import model_loader

SOVITS_DIR = Path(Path.cwd(), "sovits")


class __GitCloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm()

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()


def _load_sovits():
    if Path.exists(SOVITS_DIR):
        print("so-vits-svc folder already exists")
        return
    
    Path.mkdir(SOVITS_DIR)    
    sovits_url = "https://github.com/effusiveperiscope/so-vits-svc"
    branch_name = "eff-4.0"

    repo = Repo()
    repo.clone_from(sovits_url, SOVITS_DIR, branch=branch_name, progress=__GitCloneProgress())

    converter_path = Path(Path.cwd(), "converter.py")
    shutil.copy(converter_path, SOVITS_DIR)

    print("so-vits-svc cloned")


def _load_hubert_model():
    model_loader.download(["https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/checkpoint_best_legacy_500.pt"],
              filenames=[f"{SOVITS_DIR}/hubert/checkpoint_best_legacy_500.pt"])
    

def _load_kanye_model():
    model_loader.download(["https://mega.nz/file/Dr40kCQI#G3bEWPvUvTa9SBJKQt7rETgcFds4ssnJF0nGN9aAXTk"])



def load_dependencies():
    _load_kanye_model()