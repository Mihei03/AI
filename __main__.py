import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from src.gui.welcome import WelcomeWindow
from src.gui.separation import SeparationWindow
from src.gui.model_selection import ModelSelectionWindow

import glob
import os
from pathlib import Path
import shutil
import subprocess
import json

project_root = Path(__file__).parent
sys.path.append(str(project_root))

sovits_path = os.path.join(project_root, "src", "SOVITS", "so-vits-svc-eff-4.0")
sys.path.append(str(sovits_path))

from src.audio.audio_separation import separate, split_audio
from src.audio.audio_merging import merge
import src.utils.startup
import src.utils.model_loader
import src.utils.megadown
from src.gui.audio_processing import AudioProcessingWindow

import soundfile
import librosa

class PathManager:
    def __init__(self):
        # Получаем путь к директории AI_code
        self.ai_code_dir = Path(__file__).resolve().parent
        # Получаем путь к директории src
        self.src_dir = self.ai_code_dir / "src"
        # Создаем директорию SOVITS в src, если она не существует
        self.sovits_dir = self.src_dir / "SOVITS"
        self.sovits_dir.mkdir(parents=True, exist_ok=True)
        # Убедимся, что мы находимся в директории AI_code
        os.chdir(self.ai_code_dir)
        
    def get_path(self, *parts):
        """Создаем пути относительно директории SOVITS"""
        return self.sovits_dir.joinpath(*parts)
    
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Separation App")
        self.setGeometry(100, 100, 600, 400)
        self.path_mgr = PathManager()
        self.show_welcome_window()
        self.current_song_path = None

    def show_welcome_window(self):
        self.welcome_window = WelcomeWindow()
        self.welcome_window.process_audio_button.setEnabled(True)  # Явно включаем кнопку
        self.welcome_window.create_model_button.clicked.connect(self.on_create_model_clicked)
        self.welcome_window.process_audio_button.clicked.connect(self.show_separation_window)
        self.welcome_window.exit_button.clicked.connect(self.close)
        self.setCentralWidget(self.welcome_window)

    def on_create_model_clicked(self):
        # Ничего не делаем, просто выводим сообщение
        print("Кнопка 'Создать модель' нажата, но пока без действий.")

    def show_separation_window(self):
        self.separation_window = SeparationWindow()
        self.separation_window.back_button.clicked.connect(self.show_welcome_window)
        self.separation_window.next_button.clicked.connect(self.process_audio)
        self.setCentralWidget(self.separation_window)

    def show_model_selection_window(self):
        self.model_selection_window = ModelSelectionWindow()
        self.model_selection_window.back_button.clicked.connect(lambda: self.show_separation_window())
        self.model_selection_window.next_button.clicked.connect(self.process_model_selection)
        self.setCentralWidget(self.model_selection_window)

    def show_audio_processing_window(self, temp_song_path):
        self.audio_processing_window = AudioProcessingWindow(temp_song_path)
        self.setCentralWidget(self.audio_processing_window)

    def process_audio(self):
        self.current_song_path = self.separation_window.song_path
        if not self.separation_window.song_path:
            QMessageBox.warning(self, "Ошибка", "Выберите песню для обработки.")
            return

        song_path = self.separation_window.song_path
        split_option = int(self.separation_window.split_options.currentText().split(' - ')[0])
        save_path = self.separation_window.save_path if self.separation_window.save_path else self.path_mgr.get_path("temp")
        
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)

        temp_dir = self.path_mgr.get_path("temp")
        if Path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        Path.mkdir(temp_dir, exist_ok=True)

        input_file = Path(song_path)
        separate(split_option, input_file, temp_dir)

        QMessageBox.information(self, "Информация", f"Разделенный файл сохранен в: {save_path}")

        if self.separation_window.save_path:
            self.separation_window.next_button.setEnabled(False)
        else:
            self.show_model_selection_window()

    def process_model_selection(self):
        selected_speaker = self.model_selection_window.get_selected_speaker()
        
        if not selected_speaker:
            QMessageBox.warning(self, "Ошибка", "Выберите корректную папку с моделью.")
            return

        temp_dir = self.path_mgr.get_path("temp")
        temp_song_path = temp_dir / Path(self.separation_window.song_path).stem
        temp_raw_path = temp_song_path / "raw"

        temp_raw_path.mkdir(parents=True, exist_ok=True)

        vocals_path = temp_song_path / "vocals.wav"
        if not vocals_path.exists():
            QMessageBox.warning(self, "Ошибка", f"Файл {vocals_path} не найден. Убедитесь, что аудио было успешно разделено на предыдущем шаге.")
            return

        try:
            split_audio(vocals_path, temp_raw_path, 15)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разделить аудио: {str(e)}")
            return

        try:
            os.chdir(str(self.path_mgr.sovits_dir))
            from src.audio.audio_conversion import convert
            transpose = int(self.model_selection_window.trans_tx.text())
            cluster_ratio = float(self.model_selection_window.cluster_ratio_tx.text())
            noise_scale = float(self.model_selection_window.noise_scale_tx.text())
            convert(temp_raw_path, temp_song_path, selected_speaker, noise_scale=noise_scale, transpose=transpose, cluster_ratio=cluster_ratio)
            os.chdir(str(self.path_mgr.ai_code_dir))
            
            # Добавляем уведомление об успешной обработке
            QMessageBox.information(self, "Готово", "Обработка завершена успешно. Переходим к слиянию песен.")
            
            self.show_audio_processing_window(temp_song_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить конвертацию голоса: {str(e)}")
            return


if __name__ == "__main__":
    path_mgr = PathManager()
    
    required_dirs = ['песни', 'temp', 'models', 'output', 'hubert']
    for dir_name in required_dirs:
        dir_path = path_mgr.get_path(dir_name)
        dir_path.mkdir(parents=True, exist_ok=True)
    
    config_path = path_mgr.get_path('config.json')
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        config_data = {}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

    if "initial_setup_done" not in config_data or config_data["initial_setup_done"] != "True":
        try:
            src.utils.startup.initial_setup()
            config_data["initial_setup_done"] = "True"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
        except Exception as e:
            print("Произошла ошибка при выполнении начальной настройки")
            print(e)
            import traceback
            traceback.print_exc()
            sys.exit()

    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
