import json
import shutil
import os
from git import Repo, GitCommandError
from pathlib import Path
from git import RemoteProgress
from tqdm import tqdm
import requests
import src.utils.extraction
import zipfile

# Обновляем базовую директорию
BASE_DIR = Path(Path.cwd(), "src")
SOVITS_DIR = Path(BASE_DIR, "SOVITS")  # Изменено: SOVITS теперь основная папка
SO_VITS_DIR = Path(SOVITS_DIR, "sovits") 
MODELS_DIR = Path(SOVITS_DIR, "models")

class GitCloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm(unit="B", unit_scale=True, unit_divisor=1024)

    def update(self, op_code, cur_count, max_count=None, message=''):
        if self.pbar.total is None and max_count:
            self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()

def download_file(url, filename):
    """Функция для загрузки файлов"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file, tqdm(
        desc=filename.name,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            pbar.update(size)

def _load_sovits():
    sovits_url = "https://github.com/effusiveperiscope/so-vits-svc"
    branch_name = "eff-4.0"
    
    if os.path.exists(SO_VITS_DIR):
        print("SOVITS директория уже существует, пропускаем клонирование.")
        return

    try:
        print(f"Клонирование репозитория {sovits_url}...")
        Repo.clone_from(sovits_url, SOVITS_DIR, branch=branch_name, progress=GitCloneProgress())
    except GitCommandError as e:
        print(f"Ошибка при клонировании репозитория: {e}")
        print("Пробуем альтернативный метод загрузки...")
        
        try:
            # Используем curl или другой метод для загрузки ZIP-архива репозитория
            os.system(f"curl -L {sovits_url}/archive/refs/heads/{branch_name}.zip -o sovits.zip")
            
            # Распаковываем архив
            shutil.unpack_archive("sovits.zip", SOVITS_DIR)
            
            # Удаляем ZIP-файл
            os.remove("sovits.zip")
            
            print("Альтернативная загрузка успешно завершена.")
        except Exception as alt_e:
            print(f"Ошибка при альтернативной загрузке: {alt_e}")
            raise

def _load_hubert_model():
    hubert_dir = Path(SOVITS_DIR, "hubert")
    hubert_dir.mkdir(parents=True, exist_ok=True)
    
    hubert_url = "https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/checkpoint_best_legacy_500.pt"
    hubert_path = Path(hubert_dir, "checkpoint_best_legacy_500.pt")
    
    if not hubert_path.exists():
        download_file(hubert_url, hubert_path)

def _load_kanye_model(max_retries=3):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = Path(MODELS_DIR, "ye200k.zip")
    model_url = "https://huggingface.co/QuickWick/Music-AI-Voices/resolve/main/Kanye%20West%20200k/Kanye%20West%20ye200k.zip"
    
    for attempt in range(max_retries):
        if not model_path.exists():
            download_file(model_url, model_path)
        
        try:
            with zipfile.ZipFile(model_path, 'r') as zip_ref:
                zip_ref.testzip()
            print("Архив успешно загружен и проверен")
            break
        except zipfile.BadZipFile:
            print(f"Попытка {attempt + 1}: Загруженный архив поврежден. Пробуем снова.")
            os.remove(model_path)
            if attempt == max_retries - 1:
                print("Не удалось загрузить архив после нескольких попыток.")
                return
    
    try:
        src.utils.extraction.extract(model_path, MODELS_DIR)
        print(f"Модель успешно распакована в {MODELS_DIR}")
    except Exception as e:
        print(f"Ошибка при распаковке архива: {e}")

def initial_setup():
    try:
        _load_sovits()
        _load_hubert_model()
        _load_kanye_model()
        print("Начальная настройка завершена успешно")
    except Exception as e:
        print(f"Произошла ошибка при выполнении начальной настройки: {str(e)}")
        raise

if __name__ == "__main__":
    initial_setup()