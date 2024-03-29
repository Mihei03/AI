import shutil
from git import Repo
from pathlib import Path

from git import RemoteProgress
from tqdm import tqdm

class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm()

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()

def _load_sovits():
    sovits_directory = Path(Path.cwd(), "sovits")
    if Path.exists(sovits_directory):
        print("so-vits-svc folder already exists")
        return
    
    Path.mkdir(sovits_directory)    
    sovits_url = "https://github.com/effusiveperiscope/so-vits-svc"
    branch_name = "eff-4.0"

    repo = Repo()
    repo.clone_from(sovits_url, sovits_directory, branch=branch_name, progress=CloneProgress())

    converter_path = Path(Path.cwd(), "converter.py")
    shutil.copy(converter_path, sovits_directory)

    print("so-vits-svc cloned")


def _load_hubert_model():
    pass

def _load_kanye_model():
    pass

def load_dependencies():
    _load_sovits()
    

