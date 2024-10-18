import glob
from os.path import exists
import os
import re
import shutil
from tqdm import tqdm
import urllib.request
import gdown
import megadown

# Определяем текущую директорию и создаём путь до папки AI_code
CURRENT_DIR = os.path.dirname(__file__)
AI_CODE_DIR = os.path.join(CURRENT_DIR, "AI_code")
SOVITS_DIR = os.path.join(AI_CODE_DIR, "sovits")
MODELS_DIR = os.path.join(SOVITS_DIR, "models")

# Убедимся, что все нужные папки существуют
os.makedirs(AI_CODE_DIR, exist_ok=True)
os.makedirs(SOVITS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

def request_url_with_progress_bar(url, filename):
    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)
    
    def download_url(url, filename):
        with DownloadProgressBar(unit='B', unit_scale=True,
                                 miniters=1, desc=url.split('/')[-1]) as t:
            filename, headers = urllib.request.urlretrieve(url, filename=filename, reporthook=t.update_to)
            print("Downloaded to " + filename)
    download_url(url, filename)


def download(urls, dataset='', filenames=None, force_dl=False, username='', password='', auth_needed=False):
    assert filenames is None or len(urls) == len(filenames), f"number of urls does not match filenames. Expected {len(filenames)} urls, containing the files listed below.\n{filenames}"
    assert not auth_needed or (len(username) and len(password)), f"username and password needed for {dataset} Dataset"
    if filenames is None:
        filenames = [None, ] * len(urls)
    for i, (url, filename) in enumerate(zip(urls, filenames)):
        print(f"Downloading File from {url}")
        if filename and (not force_dl) and exists(filename):
            print(f"{filename} Already Exists, Skipping.")
            continue
        if 'drive.google.com' in url:
            assert 'https://drive.google.com/uc?id=' in url, 'Google Drive links should follow the format "https://drive.google.com/uc?id=1eQAnaoDBGQZldPVk-nzgYzRbcPSmnpv6".\nWhere id=XXXXXXXXXXXXXXXXX is the Google Drive Share ID.'
            gdown.download(url, filename, quiet=False)
        elif 'mega.nz' in url:
            print(filename)
            megadown.download(url, filename)
        else:
            request_url_with_progress_bar(url, filename)  # with progress bar

# Извлечение ZIP-архивов с моделями в директорию "models"
model_zip_paths = glob.glob(f'{MODELS_DIR}/*.zip', recursive=True)

for model_zip_path in model_zip_paths:
    print("extracting zip", model_zip_path)
    output_dir = os.path.join(MODELS_DIR, os.path.basename(os.path.splitext(model_zip_path)[0]).replace(" ", "_"))
    
    # Чистим и создаём выходную директорию
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)
    input_base = os.path.dirname(model_zip_path)

    # Очистить входной каталог (если пользователь остановил более раннюю распаковку и остались временные файлы)
    ckpts_pre = glob.glob(os.path.join(input_base, '**/*.pth'), recursive=True)
    jsons_pre = glob.glob(os.path.join(input_base, '**/config.json'), recursive=True)
    for cpkt in ckpts_pre:
        os.remove(cpkt)
    for json in jsons_pre:
        os.remove(json)

    # Делаем извлечение
    extract(model_zip_path)
    ckpts = glob.glob(os.path.join(input_base, '**/*.pth'), recursive=True)
    jsons = glob.glob(os.path.join(input_base, '**/config.json'), recursive=True)
    for ckpt in ckpts:
        shutil.move(ckpt, os.path.join(output_dir, os.path.basename(ckpt)))
    for json in jsons:
        shutil.move(json, os.path.join(output_dir, os.path.basename(json)))