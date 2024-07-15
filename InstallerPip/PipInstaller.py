from pathlib import Path
import subprocess
import sys

def install_pip():
    py_executable = sys.executable
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"

    try:
        # Загрузка скрипта get-pip.py
        subprocess.check_call([py_executable, "-c", "import urllib.request; urllib.request.urlretrieve('{}', 'get-pip.py')".format(get_pip_url)])
        # Установка pip
        subprocess.check_call([py_executable, "get-pip.py"])
        print("pip успешно установлен.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке pip: {e}")
    finally:
        # Удаление временного файла get-pip.py
        try:
            import os
            os.remove("get-pip.py")
        except:
            pass
        
    #subprocess.run(["pip", "install", "gitpython"])
    #subprocess.run(["pip", "install", "gdown"])
    #subprocess.run(["pip", "install", "patool"])
    requirements_file = "D:/все_папки/AI/InstallerPip/requirements_win.txt"
    install_from_requirements(requirements_file)
    subprocess.run(["pip", "install", "spleeter"])
    subprocess.run(["pip", "install", "ffmpeg-python"])
    subprocess.run(["pip", "install", "pyworld"]) #Вроде есть в txt фалйле, но почему то у меня не подгрузило
    subprocess.run(["pip", "install", "praat-parselmouth"]) #Вроде есть в txt фалйле, но почему то у меня не подгрузило
    #install_pip() #Просто нужно, иначе пипы полетят
    #subprocess.run(["pip", "install", "fairseq==0.12.2"])  #Вроде есть в txt фалйле, но почему то у меня не подгрузило
    subprocess.run(["pip", "install", "librosa==0.8.1"]) #Разные версии librosa, ну хз-хз
    subprocess.run(["pip", "install", "numpy==1.23.5"])  #Разные версии numpy, ну хз-хз

def install_from_requirements(requirements_file):
    import pip
    if not Path(requirements_file).exists():
        print(f"Файл {requirements_file} не существует.")
        return

    with open(requirements_file, "r") as f:
        requirements = f.read().splitlines()

    for line in requirements:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("--"):
            try:
                if hasattr(pip, 'main'):
                    pip.main(['install', line])
                else:
                    pip._internal.main(['install', line])
                print(f"Успешно установлен пакет: {line}")
            except Exception as e:
                print(f"Ошибка при установке {line}: {e}")

# Использование
install_pip()
