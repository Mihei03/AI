import sys
import tarfile
import os
from zipfile import ZipFile
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QLabel, QLineEdit, QCheckBox, QPushButton
import io  # Импортируем модуль io для работы с BytesIO

# taken from https://github.com/CookiePPP/cookietts/blob/master/CookieTTS/utils/dataset/extract_unknown.py
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

# taken from https://github.com/CookiePPP/cookietts/tree/master/CookieTTS/_0_download/scripts

# megatools download urls
win64_url = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-win64.zip"
win32_url = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-win32.zip"
linux_url = "https://megatools.megous.com/builds/builds/megatools-1.11.1.20230212-linux-x86_64.tar.gz"
# download megatools
from sys import platform
import os
import urllib.request
import subprocess
from time import sleep

if platform == "linux" or platform == "linux2":
        dl_url = linux_url
elif platform == "darwin":
    raise NotImplementedError('MacOS not supported.')
elif platform == "win32":
        dl_url = win64_url
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


binary_folder = os.path.abspath(binary_folder)

def megadown(download_link, filename='.', verbose=False):
    """Use megatools binary executable to download files and folders from MEGA.nz ."""
    filename = ' --path "'+os.path.abspath(filename)+'"' if filename else ""
    wd_old = os.getcwd()
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

import urllib.request
from tqdm import tqdm
import gdown
from os.path import exists

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
            print("Downloaded to "+filename)
    download_url(url, filename)


def download(urls, dataset='', filenames=None, force_dl=False, username='', password='', auth_needed=False):
    assert filenames is None or len(urls) == len(filenames), f"number of urls does not match filenames. Expected {len(filenames)} urls, containing the files listed below.\n{filenames}"
    assert not auth_needed or (len(username) and len(password)), f"username and password needed for {dataset} Dataset"
    if filenames is None:
        filenames = [None,]*len(urls)
    for i, (url, filename) in enumerate(zip(urls, filenames)):
        print(f"Downloading File from {url}")
        #if filename is None:
        #    filename = url.split("/")[-1]
        if filename and (not force_dl) and exists(filename):
            print(f"{filename} Already Exists, Skipping.")
            continue
        if 'drive.google.com' in url:
            assert 'https://drive.google.com/uc?id=' in url, 'Google Drive links should follow the format "https://drive.google.com/uc?id=1eQAnaoDBGQZldPVk-nzgYzRbcPSmnpv6".\nWhere id=XXXXXXXXXXXXXXXXX is the Google Drive Share ID.'
            gdown.download(url, filename, quiet=False)
        elif 'mega.nz' in url:
            megadown(url, filename)
        else:
            #urllib.request.urlretrieve(url, filename=filename) # no progress bar
            request_url_with_progress_bar(url, filename) # with progress bar

import huggingface_hub
import os
import shutil

class HFModels:
    def __init__(self, repo = "therealvul/so-vits-svc-4.0", 
            model_dir = "hf_vul_models"):
        self.model_repo = huggingface_hub.Repository(local_dir=model_dir,
            clone_from=repo, skip_lfs_files=True)
        self.repo = repo
        self.model_dir = model_dir

        self.model_folders = os.listdir(model_dir)
        self.model_folders.remove('.git')
        self.model_folders.remove('.gitattributes')

    def list_models(self):
        return self.model_folders

    # Downloads model;
    # copies config to target_dir and moves model to target_dir
    def download_model(self, model_name, target_dir):
        if not model_name in self.model_folders:
            raise Exception(model_name + " not found")
        model_dir = self.model_dir
        charpath = os.path.join(model_dir,model_name)

        gen_pt = next(x for x in os.listdir(charpath) if x.startswith("G_"))
        cfg = next(x for x in os.listdir(charpath) if x.endswith("json"))
        try:
          clust = next(x for x in os.listdir(charpath) if x.endswith("pt"))
        except StopIteration as e:
          print("Note - no cluster model for "+model_name)
          clust = None

        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        gen_dir = huggingface_hub.hf_hub_download(repo_id = self.repo,
            filename = model_name + "/" + gen_pt) # this is a symlink
        
        if clust is not None:
          clust_dir = huggingface_hub.hf_hub_download(repo_id = self.repo,
              filename = model_name + "/" + clust) # this is a symlink
          shutil.move(os.path.realpath(clust_dir), os.path.join(target_dir, clust))
          clust_out = os.path.join(target_dir, clust)
        else:
          clust_out = None

        shutil.copy(os.path.join(charpath,cfg),os.path.join(target_dir, cfg))
        shutil.move(os.path.realpath(gen_dir), os.path.join(target_dir, gen_pt))

        return {"config_path": os.path.join(target_dir,cfg),
            "generator_path": os.path.join(target_dir,gen_pt),
            "cluster_path": clust_out}

# Example usage
# vul_models = HFModels()
# print(vul_models.list_models())
# print("Applejack (singing)" in vul_models.list_models())
# vul_models.download_model("Applejack (singing)","models/Applejack (singing)")
os.chdir(r'C:\Users\mihei\Desktop\so-vits-svc') # force working-directory to so-vits-svc - this line is just for safety and is probably not required
download(["https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/checkpoint_best_legacy_500.pt"], filenames=["hubert/checkpoint_best_legacy_500.pt"])
print("Finished!")


import re
# Получение URL-адреса модели из параметра или загрузка из Hugging Face
model_url = "https://mega.nz/file/Dr40kCQI#G3bEWPvUvTa9SBJKQt7rETgcFds4ssnJF0nGN9aAXTk" #@param {"type": "string"}
if "huggingface.co" in model_url.lower():
  download([re.sub(r"/blob/","/resolve/",model_url)], 
           filenames=[os.path.join(os.getcwd(),model_url.split("/")[-1])])
else:
  download([model_url])


# Извлечение ZIP-архивов с моделями в директорию "models"
import glob, os, shutil
from pathlib import Path

os.makedirs('models', exist_ok=True)
model_zip_paths = glob.glob(r'C:\Users\mihei\Desktop\so-vits-svc\models*.zip', recursive=True) #Не уверен, что тут нужен именно этот путь!?

for model_zip_path in model_zip_paths:
    print("extracting zip",model_zip_path)
    output_dir = os.path.join(r'C:\Users\mihei\Desktop\so-vits-svc\models',os.path.basename(os.path.splitext(model_zip_path)[0]).replace(" ","_"))
    
    # clean and create output dir (код для извлечения ZIP-архивов)
    if os.path.exists(output_dir):
      shutil.rmtree(output_dir)
    os.mkdir(output_dir)
    input_base = os.path.dirname(model_zip_path)

    # очистить входной каталог (если пользователь остановил более раннюю распаковку и у нас есть грязные файлы)
    ckpts_pre = glob.glob(os.path.join(input_base,'**/*.pth'),recursive=True)
    jsons_pre = glob.glob(os.path.join(input_base,'**/config.json'),recursive=True)
    for cpkt in ckpts_pre:
      os.remove(cpkt)
    for json in jsons_pre:
      os.remove(json)

    # делаем извлечение
    extract(model_zip_path)
    ckpts = glob.glob(os.path.join(input_base,'**/*.pth'),recursive=True)
    jsons = glob.glob(os.path.join(input_base,'**/config.json'),recursive=True)
    for ckpt in ckpts:
      shutil.move(ckpt,os.path.join(output_dir,os.path.basename(ckpt)))
    for json in jsons:
      shutil.move(json,os.path.join(output_dir,os.path.basename(json)))


import os
import glob
import json
import copy
import logging
from PyQt5.QtCore import Qt
import torch
from inference import infer_tool
from inference import slicer
from inference.infer_tool import Svc
import soundfile
import numpy as np

MODELS_DIR = r"C:\Users\mihei\Desktop\so-vits-svc\models"

# Получение списка доступных моделей (динамиков)

def get_speakers():
  speakers = []
  for _,dirs,_ in os.walk(MODELS_DIR):
    for folder in dirs:
        # ... (код для получения информации о модели)
      cur_speaker = {}
      # Ищем G_****.pth
      g = glob.glob(os.path.join(MODELS_DIR,folder,'G_*.pth'))
      if not len(g):
        print("Skipping "+folder+", no G_*.pth")
        continue
      cur_speaker["model_path"] = g[0]
      cur_speaker["model_folder"] = folder

      # Ищем *.pt (модель кластеризации)
      clst = glob.glob(os.path.join(MODELS_DIR,folder,'*.pt'))
      if not len(clst):
        print("Note: No clustering model found for "+folder)
        cur_speaker["cluster_path"] = ""
      else:
        cur_speaker["cluster_path"] = clst[0]

      # Ищем config.json
      cfg = glob.glob(os.path.join(MODELS_DIR,folder,'*.json'))
      if not len(cfg):
        print("Skipping "+folder+", no config json")
        continue
      cur_speaker["cfg_path"] = cfg[0]
      with open(cur_speaker["cfg_path"]) as f:
        try:
          cfg_json = json.loads(f.read())
        except Exception as e:
          print("Malformed config json in "+folder)
        for name, i in cfg_json["spk"].items():
          cur_speaker["name"] = name
          cur_speaker["id"] = i
          if not name.startswith('.'):
            speakers.append(copy.copy(cur_speaker))

    return sorted(speakers, key=lambda x:x["name"].lower())

# Настройка логгирования и других параметров
logging.getLogger('numba').setLevel(logging.WARNING)
chunks_dict = infer_tool.read_temp("inference/chunks_temp.json") #Не уверен, что это такое?... Откуда это нужно брать...
existing_files = []
slice_db = -40
wav_format = 'wav'

class InferenceGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inference GUI")
        
        # Получение списка моделей (динамиков)
        self.speakers = get_speakers()
        
         # Создание виджетов GUI (комбобокс, поля ввода, кнопки и т.д.)
        self.speaker_label = QLabel("Модели голоса:")
        self.speaker_box = QComboBox()
        self.speaker_box.addItems([x["name"] for x in self.speakers])
        
        self.trans_label = QLabel("Высота тона (хороший диапазон от -12 до 12):")
        self.trans_tx = QLineEdit()
        self.trans_tx.setText("0")
        
        self.cluster_ratio_label = QLabel("Соотношение между звучанием, похожим на тембр цели, \nчеткостью и артикулированностью, чтобы найти подходящий компромисс:")
        self.cluster_ratio_tx = QLineEdit()
        self.cluster_ratio_tx.setText("0.0")
        
        self.noise_scale_label = QLabel("Если выходной сигнал звучит гулко, попробуйте увеличить масштаб шума:")
        self.noise_scale_tx = QLineEdit()
        self.noise_scale_tx.setText("0.4")
        
        self.auto_pitch_ck = QCheckBox("Автоматическое предсказание высоты тона. \nОставьте этот флажок не отмеченным, если вы конвертируете певческий голос.")
        
        self.convert_btn = QPushButton("Конвертировать")
        self.convert_btn.clicked.connect(self.convert)
        
        self.clean_btn = QPushButton("Удалить все аудиофайлы")
        self.clean_btn.clicked.connect(self.clean)
        
        # Создание макета и центрального виджета
        layout = QVBoxLayout()
        layout.addWidget(self.speaker_label)
        layout.addWidget(self.speaker_box)
        layout.addWidget(self.trans_label)
        layout.addWidget(self.trans_tx)
        layout.addWidget(self.cluster_ratio_label)
        layout.addWidget(self.cluster_ratio_tx)
        layout.addWidget(self.noise_scale_label)
        layout.addWidget(self.noise_scale_tx)
        layout.addWidget(self.auto_pitch_ck)
        layout.addWidget(self.convert_btn)
        layout.addWidget(self.clean_btn)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    # Функция для преобразования аудиофайлов
    def convert(self):
        trans = int(self.trans_tx.text())
        speaker = next(x for x in self.speakers if x["name"] == self.speaker_box.currentText())
        svc_model = Svc(speaker["model_path"], speaker["cfg_path"], cluster_model_path=speaker["cluster_path"])

        input_filepaths = [f for f in glob.glob(r'C:\Users\mihei\Desktop\Цой\vocals.*', recursive=True)
                            if f not in existing_files and
                            any(f.endswith(ex) for ex in ['.wav', '.flac', '.mp3', '.ogg', '.opus'])]
        for name in input_filepaths:
            print("Converting " + os.path.split(name)[-1])
            infer_tool.format_wav(name)
            wav_path = str(Path(name).with_suffix('.wav'))
            wav_name = Path(name).stem
            chunks = slicer.cut(wav_path, db_thresh=slice_db)
            audio_data, audio_sr = slicer.chunks2audio(wav_path, chunks)

            audio = []
            for (slice_tag, data) in audio_data:
                print(f'#=====segment start, {round(len(data)/audio_sr, 3)}s======')
                length = int(np.ceil(len(data) / audio_sr * svc_model.target_sample))

                if slice_tag:
                    print('jump empty segment')
                    _audio = np.zeros(length)
                else:
                    pad_len = int(audio_sr * 0.5)
                    data = np.concatenate([np.zeros([pad_len]), data, np.zeros([pad_len])])
                    raw_path = io.BytesIO()  # Создаем объект BytesIO
                    soundfile.write(raw_path, data, audio_sr, format="wav")
                    raw_path.seek(0)
                    _cluster_ratio = 0.0
                    if speaker["cluster_path"] != "":
                        _cluster_ratio = float(self.cluster_ratio_tx.text())
                    out_audio, out_sr = svc_model.infer(
                        speaker["name"], trans, raw_path,
                        cluster_infer_ratio=_cluster_ratio,
                        auto_predict_f0=self.auto_pitch_ck.isChecked(),
                        noice_scale=float(self.noise_scale_tx.text()))
                    _audio = out_audio.cpu().numpy()
                    pad_len = int(svc_model.target_sample * 0.5)
                    _audio = _audio[pad_len:-pad_len]
                audio.extend(list(infer_tool.pad_array(_audio, length)))

            res_path = os.path.join(r'C:\Users\mihei\Desktop\Цой', f'{wav_name}_{trans}_key_{speaker["name"]}.{wav_format}')
            soundfile.write(res_path, audio, svc_model.target_sample, format=wav_format)
            print(f"Converted audio saved to {res_path}")  # Добавляем вывод сообщения о сохранении файла
            # display(Audio(res_path, autoplay=True))  # Удалено, так как это специфично для Jupyter Notebook
            
    # Функция для удаления аудиофайлов
    def clean(self):
        input_filepaths = [f for f in glob.glob(r'C:\Users\mihei\Desktop\Цой\*.*', recursive=True)
                            if f not in existing_files and
                            any(f.endswith(ex) for ex in ['.wav', '.flac', '.mp3', '.ogg', '.opus'])]
        for f in input_filepaths:
            os.remove(f)
            
# Создание и запуск приложения GUI
if __name__ == "__main__":
    app = QApplication(sys.argv)
    inference_gui = InferenceGui()
    inference_gui.show()
    sys.exit(app.exec_())
