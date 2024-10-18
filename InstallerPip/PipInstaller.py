import os
import subprocess
import sys
from pathlib import Path

def get_parent_dir():
    """Получение пути к родительской директории"""
    current_dir = Path(__file__).resolve().parent  # Текущая директория (InstallerPip)
    return current_dir.parent  # Родительская директория

def create_virtual_environment():
    """Создание виртуальной среды в родительской директории, если она не существует"""
    parent_dir = get_parent_dir()
    venv_path = parent_dir / "AI_venv"
    
    if not venv_path.exists():
        print(f"Создание виртуальной среды 'AI_venv' в директории {parent_dir}...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
            print("Виртуальная среда успешно создана.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при создании виртуальной среды: {e}")
            sys.exit(1)
    else:
        print("Виртуальная среда 'AI_venv' уже существует.")

def get_venv_python():
    """Получение пути к исполняемому файлу Python из виртуальной среды"""
    parent_dir = get_parent_dir()
    # Определяем путь в зависимости от операционной системы
    if sys.platform == "win32":
        python_path = parent_dir / "AI_venv/Scripts/python.exe"
    else:
        python_path = parent_dir / "AI_venv/bin/python"
    return str(python_path.absolute())

def install_pip():
    """Установка pip в виртуальной среде, если необходимо"""
    python_exe = get_venv_python()
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    parent_dir = get_parent_dir()
    get_pip_path = parent_dir / "get-pip.py"

    try:
        # Загрузка скрипта get-pip.py
        subprocess.check_call([
            python_exe, 
            "-c", 
            f"import urllib.request; urllib.request.urlretrieve('{get_pip_url}', '{str(get_pip_path)}')"
        ])
        # Установка pip
        subprocess.check_call([python_exe, str(get_pip_path)])
        print("pip успешно установлен в виртуальной среде.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке pip: {e}")
        sys.exit(1)
    finally:
        # Удаление временного файла get-pip.py
        try:
            get_pip_path.unlink()
        except:
            pass

def install_requirements():
    """Установка пакетов из файла requirements.txt"""
    python_exe = get_venv_python()
    current_dir = Path(__file__).resolve().parent
    requirements_file = current_dir / "requirements.txt"

    # Проверка наличия файла requirements.txt
    if not requirements_file.exists():
        print(f"Ошибка: файл {requirements_file} не найден в директории InstallerPip.")
        sys.exit(1)

    print("Установка зависимостей из файла requirements.txt...")
    try:
        # Установка всех пакетов из requirements.txt
        subprocess.check_call([
            python_exe, 
            "-m", 
            "pip", 
            "install", 
            "-r", 
            str(requirements_file)
        ])
        print("Все зависимости успешно установлены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке зависимостей: {e}")
        sys.exit(1)

def main():
    # Создаем виртуальную среду
    create_virtual_environment()
    
    # Устанавливаем/обновляем pip
    install_pip()
    
    # Устанавливаем зависимости
    install_requirements()

if __name__ == "__main__":
    main()
