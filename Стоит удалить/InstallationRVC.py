import os
import sys
import torch
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal

class InstallationThread(QThread):
    download_progress = pyqtSignal(int)
    installation_complete = pyqtSignal()

    def run(self):
        # Проверка подключения к GPU
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
            print("\nGPU недоступен!\n")
            print("Вычисления будут выполняться на CPU. Это может замедлить процесс и привести к ошибкам.\n")

        # Клонирование репозитория
        repo_url = "https://github.com/Bebra777228/TrainVocModel.git"
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\RVC')
        repo_path = os.path.join(desktop_path, "TrainVocModel")

        try:
            os.system(f"git clone {repo_url} {repo_path}")
        except Exception as e:
            print(f"Ошибка при клонировании репозитория: {e}")
            self.installation_complete.emit()
            return

        # Установка зависимостей
        requirements_file = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(requirements_file):
            try:
                os.system(f"pip install -r {requirements_file}")
            except Exception as e:
                print(f"Ошибка при установке зависимостей: {e}")
        else:
            print("Файл requirements.txt не найден.")

        self.installation_complete.emit()

class InstallationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.progress_label = QLabel("Установка...")
        layout.addWidget(self.progress_label)

        self.install_button = QPushButton("Установить")
        self.install_button.clicked.connect(self.start_installation)
        layout.addWidget(self.install_button)

        self.setLayout(layout)
        self.setWindowTitle("Установка RVC")

    def start_installation(self):
        self.install_thread = InstallationThread()
        self.install_thread.installation_complete.connect(self.installation_complete)
        self.install_thread.start()
        self.install_button.setEnabled(False)

    def installation_complete(self):
        self.progress_label.setText("Установка завершена!")
        self.install_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstallationWindow()
    window.show()
    sys.exit(app.exec_())