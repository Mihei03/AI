import glob
import os
import re
import shutil
from tqdm import tqdm
import urllib.request
import gdown
from pathlib import Path

# Обновляем базовую директорию
BASE_DIR = Path(__file__).resolve().parent.parent / "SOVITS"
SOVITS_DIR = BASE_DIR
MODELS_DIR = BASE_DIR / "models"

def request_url_with_progress_bar(url, filename):
    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)
    
    def download_url(url, filename):
        with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
            filename, headers = urllib.request.urlretrieve(url, filename=filename, reporthook=t.update_to)
            print("Загружено в "+filename)
    download_url(url, filename)

def download(urls, dataset='', filenames=None, force_dl=False, username='', password='', auth_needed=False):
    assert filenames is None or len(urls) == len(filenames), f"Количество URL не соответствует количеству имен файлов. Ожидалось {len(filenames)} URL, содержащих файлы, перечисленные ниже.\n{filenames}"
    assert not auth_needed or (len(username) and len(password)), f"Требуется имя пользователя и пароль для набора данных {dataset}"
    if filenames is None:
        filenames = [None,]*len(urls)
    for i, (url, filename) in enumerate(zip(urls, filenames)):
        print(f"Загрузка файла с {url}")
        if filename and (not force_dl) and os.path.exists(filename):
            print(f"{filename} уже существует, пропускаем.")
            continue
        if 'drive.google.com' in url:
            assert 'https://drive.google.com/uc?id=' in url, 'Ссылки Google Drive должны соответствовать формату "https://drive.google.com/uc?id=1eQAnaoDBGQZldPVk-nzgYzRbcPSmnpv6".\nГде id=XXXXXXXXXXXXXXXXX - это ID общего доступа Google Drive.'
            gdown.download(url, filename, quiet=False)
        elif 'mega.nz' in url:
            print(filename)
            from megadown import download
            download(url, filename)
        else:
            request_url_with_progress_bar(url, filename)

# Создаем необходимые директории
os.makedirs(MODELS_DIR, exist_ok=True)

# Получение URL-адреса модели из параметра или загрузка из Hugging Face
# if "huggingface.co" in model_url.lower():
    # download([re.sub(r"/blob/","/resolve/",model_url)], 
        #    filenames=[os.path.join(os.getcwd(), model_url.split("/")[-1])])


# Извлечение ZIP-архивов с моделями в директорию "models"
model_zip_paths = glob.glob(os.path.join(SOVITS_DIR, 'models*.zip'), recursive=True)

for model_zip_path in model_zip_paths:
    print("Извлечение zip", model_zip_path)
    output_dir = os.path.join(MODELS_DIR, os.path.basename(os.path.splitext(model_zip_path)[0]).replace(" ","_"))
    
    # Очищаем и создаем выходную директорию
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    input_base = os.path.dirname(model_zip_path)

    # Очищаем входной каталог
    ckpts_pre = glob.glob(os.path.join(input_base,'**/*.pth'), recursive=True)
    jsons_pre = glob.glob(os.path.join(input_base,'**/config.json'), recursive=True)
    for cpkt in ckpts_pre:
        os.remove(cpkt)
    for json in jsons_pre:
        os.remove(json)

    # Выполняем извлечение
    from extraction import extract
    extract(model_zip_path)
    ckpts = glob.glob(os.path.join(input_base,'**/*.pth'), recursive=True)
    jsons = glob.glob(os.path.join(input_base,'**/config.json'), recursive=True)
    for ckpt in ckpts:
        shutil.move(ckpt, os.path.join(output_dir, os.path.basename(ckpt)))
    for json in jsons:
        shutil.move(json, os.path.join(output_dir, os.path.basename(json)))