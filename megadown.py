from pathlib import Path
import subprocess
from time import sleep
import urllib.request
from sys import *
import os

from extract import extract

WIN64_URL = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-win64.zip"
WIN32_URL = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-win32.zip"
LINUX_URL = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-linux-x86_64.tar.gz"


def __download_megatools():
    if platform == "linux" or platform == "linux2":
            dl_url = LINUX_URL
    elif platform == "darwin":
        raise NotImplementedError('MacOS not supported.')
    elif platform == "win32":
            dl_url = WIN64_URL
    else:
        raise NotImplementedError ('Unknown Operating System.')

    dlname = dl_url.split("/")[-1]
    if dlname.endswith(".zip"):
        binary_folder = dlname[:-4] # remove .zip
    elif dlname.endswith(".tar.gz"):
        binary_folder = dlname[:-7] # remove .tar.gz
    else:
        raise NameError('downloaded megatools has unknown archive file extension!')

    if not os.path.exists(binary_folder):
        print('"megatools" not found. Downloading...')
        if not os.path.exists(dlname):
            urllib.request.urlretrieve(dl_url, dlname)
        assert os.path.exists(dlname), 'failed to download.'
        extract(dlname)
        sleep(0.10)
        os.unlink(dlname)
        print("Done!")

    return binary_folder

def download(url, target_directory='.', verbose=False):
    if target_directory:
         target_directory = f"--path {Path.absolute(target_directory)}"

    binaries_map = {
         "linux": "./megatools",
         "linux2": "./megatools",
         "win32": "megatools.exe"
    }

    binary_folder = Path(__download_megatools()).resolve()
    binary_name = binaries_map[platform]
    binary_path = Path(binary_folder, binary_name)
    
    verbose_arg = ""
    if verbose:
        verbose_arg = "--debug http"

    subprocess.call(f"{binary_path} dl {url} {target_directory} {verbose_arg}", shell=True)
    
    return target_directory
