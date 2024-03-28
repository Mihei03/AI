import subprocess
import tarfile
from time import sleep
import urllib.request
from sys import *
from zipfile import ZipFile
import os

WIN64_URL = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-win64.zip"
WIN32_URL = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-win32.zip"
LINUX_URL = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-linux-x86_64.tar.gz"

def extract(path):
    if path.endswith(".zip"):
        with ZipFile(path, 'r') as zipObj:
           zipObj.extractall(os.path.split(path)[0])
    elif path.endswith(".tar.bz2"):
        tar = tarfile.open(path, "r:bz2")
        tar.extractall(os.path.split(path)[0])
        tar.close()
    elif path.endswith(".tar.gz"):
        tar = tarfile.open(path, "r:gz")
        tar.extractall(os.path.split(path)[0])
        tar.close()
    elif path.endswith(".tar"):
        tar = tarfile.open(path, "r:")
        tar.extractall(os.path.split(path)[0])
        tar.close()
    elif path.endswith(".7z"):
        import py7zr
        archive = py7zr.SevenZipFile(path, mode='r')
        archive.extractall(path=os.path.split(path)[0])
        archive.close()
    else:
        raise NotImplementedError(f"{path} extension not implemented.")


def download_megatools():
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

def megadown(download_link, filename='.', verbose=False):
    """Use megatools binary executable to download files and folders from MEGA.nz ."""
    filename = ' --path "'+os.path.abspath(filename)+'"' if filename else ""
    wd_old = os.getcwd()
    binary_folder = os.path.abspath(download_megatools())


    os.chdir(binary_folder)
    try:
        if platform == "linux" or platform == "linux2":
            subprocess.call(f'./megatools dl{filename}{" --debug http" if verbose else ""} {download_link}', shell=True)
        elif platform == "win32":
            subprocess.call(f'megatools.exe dl{filename}{" --debug http" if verbose else ""} {download_link}', shell=True)
    except:
        os.chdir(wd_old) # don't let user stop download without going back to correct directory first
        raise
    os.chdir(wd_old)
    return filename
