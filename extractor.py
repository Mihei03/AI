import os
from pathlib import Path
import zipfile
import tarfile
import patoolib

def extract(file_path, target_dir):
    file_path = str(file_path)
    if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            zip_file.extractall(target_dir)
    elif file_path.endswith(".tar"):
        with tarfile.open(file_path, 'r') as tar_file:
            tar_file.extractall(target_dir)
    elif file_path.endswith(".rar"):
        try:
            patoolib.extract_archive(file_path, target_dir)
        except Exception as e:
            print(f"Не удалось распаковать RAR-архив: {e}")
    else:
        raise ValueError("Неизвестный формат архива.")