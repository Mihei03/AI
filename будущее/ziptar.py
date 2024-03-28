import os
import zipfile
import tarfile
import patoolib

def Archiver(file_path, target_dir):
    # Создать папку "AI Covers", если она не существует
    os.makedirs(os.path.join(target_dir, "AI Covers"), exist_ok=True)

    # Распаковать архив в папку "AI Covers"
    if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            zip_file.extractall(os.path.join(target_dir, "AI Covers"))
    elif file_path.endswith(".tar"):
        with tarfile.open(file_path, 'r') as tar_file:
            tar_file.extractall(os.path.join(target_dir, "AI Covers"))
    elif file_path.endswith(".rar"):
        try:
            patoolib.extract_archive(file_path, outdir=os.path.join(target_dir, "AI Covers"))
        except Exception as e:
            print(f"Не удалось распаковать RAR-архив: {e}")
    else:
        raise ValueError("Неизвестный формат архива.")

Archiver(r"C:\Users\mihei\Desktop\ИС.rar", r"C:\Users\mihei\Documents")
