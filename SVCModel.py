import os
import sys
import subprocess
import requests
import shutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QFileDialog, QCheckBox

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.clone_label = QLabel("Клон:")
        self.clone_input = QLineEdit()
        self.clone_input.setText("44k")

        self.tensorboard_checkbox = QCheckBox("Включить Tensorboard")
        self.tensorboard_checkbox.setChecked(True)

        self.install_button = QPushButton("Установить зависимости")
        self.install_button.clicked.connect(self.install_dependencies)

        self.prepare_button = QPushButton("Подготовить датасет")
        self.prepare_button.clicked.connect(self.prepare_dataset)

        self.train_button = QPushButton("Запустить тренировку")
        self.train_button.clicked.connect(self.start_training)

        layout.addWidget(self.clone_label)
        layout.addWidget(self.clone_input)
        layout.addWidget(self.tensorboard_checkbox)
        layout.addWidget(self.install_button)
        layout.addWidget(self.prepare_button)
        layout.addWidget(self.train_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def install_dependencies(self):
        subprocess.run(["pip", "install", "pyworld"])
        subprocess.run(["pip", "install", "praat-parselmouth"])
        subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.run(["pip", "install", "fairseq==0.12.2", "--user"])
        subprocess.run(["pip", "install", "librosa==0.8.1"])
        subprocess.run(["pip", "install", "numpy==1.23.5"])

        # Создание директории hubert/, если она не существует
        os.makedirs("sovits/hubert/", exist_ok=True)

        # Проверка наличия checkpoint_best_legacy_500.pt
        checkpoint_path = "sovits/hubert/checkpoint_best_legacy_500.pt"
        if not os.path.exists(checkpoint_path):
            print("Загрузка checkpoint_best_legacy_500.pt...")
            url = "https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/checkpoint_best_legacy_500.pt"
            response = requests.get(url)
            with open(checkpoint_path, "wb") as f:
                f.write(response.content)
        else:
            print("checkpoint_best_legacy_500.pt уже существует.")

        os.makedirs("sovits/logs/44k/", exist_ok=True)
        g_0_path = "sovits/logs/44k/G_0.pth"
        d_0_path = "sovits/logs/44k/D_0.pth"

        if not os.path.exists(g_0_path):
            print("Загрузка G_0.pth...")
            url = "https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/G_0.pth"
            response = requests.get(url)
            with open(g_0_path, "wb") as f:
                f.write(response.content)
        else:
            print("G_0.pth уже существует.")

        if not os.path.exists(d_0_path):
            print("Загрузка D_0.pth...")
            url = "https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/D_0.pth"
            response = requests.get(url)
            with open(d_0_path, "wb") as f:
                f.write(response.content)
        else:
            print("D_0.pth уже существует.")

        print("Всё установлено!")

    def prepare_dataset(self):
        dataset_path = QFileDialog.getExistingDirectory(self, "Выберите папку с датасетом")
        if dataset_path:
            os.makedirs("sovits/dataset_raw/", exist_ok=True)

            # Проверка на наличие файлов в папке назначения
            dataset_dest_path_raw = "sovits/dataset_raw/YouModel"
            if os.path.exists(dataset_dest_path_raw):
                print("Папка назначения уже существует. Пропускаем копирование.")
            else:
                shutil.copytree(dataset_path, dataset_dest_path_raw)

            dataset_dest_path_44k = "sovits/dataset/44k/YouModel"
            if os.path.exists(dataset_dest_path_44k):
                print("Папка назначения уже существует. Пропускаем копирование.")
            else:
                shutil.copytree(dataset_path, dataset_dest_path_44k)

            os.chdir("sovits")
            subprocess.run(["python", "resample.py"], shell=True,  check=False)
            print("Ресэмплинг завершен.")
            
            subprocess.run(["python", "preprocess_flist_config.py"], shell=True)
            print("Создание списков файлов завершено.")

            #Работа над этим файлом
            subprocess.run(["python", "preprocess_hubert_f0.py"], shell=True)
            print("Предобработка Hubert и F0 завершена.")

            print("&&&&")

    def start_training(self):
        clone = self.clone_input.text()
        tensorboard_on = self.tensorboard_checkbox.isChecked()
        os.chdir("sovits")
        if tensorboard_on:
            subprocess.Popen(["tensorboard", "--logdir", f"logs/{clone}"], shell=True)
        subprocess.run(["python", "train.py", "-c", "configs/config.json", "-m", clone])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())