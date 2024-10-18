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

from src.audio.audio_separation import separate, split_audio
from src.audio.audio_merging import merge
import src.utils.startup

import soundfile
import librosa

class PathManager:
    def __init__(self):
        # Get the AI_code directory path
        self.ai_code_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        # Ensure we're in the AI_code directory
        os.chdir(self.ai_code_dir)
        
    def get_path(self, *parts):
        """Create paths relative to AI_code directory"""
        return Path(self.ai_code_dir, *parts)
    
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Separation App")
        self.setGeometry(100, 100, 600, 400)

        self.show_welcome_window()

    def show_welcome_window(self):
        self.welcome_window = WelcomeWindow()
        self.welcome_window.start_button.clicked.connect(self.show_separation_window)
        self.welcome_window.exit_button.clicked.connect(self.close)
        self.setCentralWidget(self.welcome_window)

    def show_separation_window(self):
        self.separation_window = SeparationWindow()
        self.separation_window.back_button.clicked.connect(self.show_welcome_window)
        self.separation_window.next_button.clicked.connect(self.process_audio)
        self.setCentralWidget(self.separation_window)

    def show_model_selection_window(self):
        self.model_selection_window = ModelSelectionWindow()
        self.model_selection_window.populate_models(self.get_speakers(Path.cwd() / "models"))
        self.model_selection_window.back_button.clicked.connect(self.show_separation_window)
        self.model_selection_window.next_button.clicked.connect(self.process_model_selection)
        self.setCentralWidget(self.model_selection_window)

    def process_audio(self):
        if not self.separation_window.song_path:
            QMessageBox.warning(self, "Ошибка", "Выберите песню для обработки.")
            return

        song_path = self.separation_window.song_path
        split_option = int(self.separation_window.split_options.currentText().split(' - ')[0])
        save_path = self.separation_window.save_path if self.separation_window.save_path else Path.cwd() / "temp"
        
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)

        temp_dir = Path.cwd() / "temp"
        if Path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        Path.mkdir(temp_dir, exist_ok=True)

        input_file = Path(song_path)
        separate(split_option, input_file, temp_dir)

        # Убрано оповещение о выбранной песне
        QMessageBox.information(self, "Информация", f"Разделенный файл сохранен в: {save_path}")

        if self.separation_window.save_path:
            self.separation_window.next_button.setEnabled(False)
        else:
            self.show_model_selection_window()

    def process_model_selection(self):
        selected_model = self.model_selection_window.model_combobox.currentText()
        selected_speaker = next((s for s in self.get_speakers(Path.cwd() / "models") if s["name"] == selected_model), None)
        
        if not selected_speaker:
            QMessageBox.warning(self, "Ошибка", "Выбранная модель не найдена.")
            return

        temp_dir = Path.cwd() / "temp"
        temp_song_path = temp_dir / Path(self.separation_window.song_path).stem
        temp_raw_path = temp_song_path / "raw"

        # Убедимся, что папка raw существует
        temp_raw_path.mkdir(parents=True, exist_ok=True)

        vocals_path = temp_song_path / "vocals.wav"
        if not vocals_path.exists():
            QMessageBox.warning(self, "Ошибка", f"Файл {vocals_path} не найден. Убедитесь, что аудио было успешно разделено на предыдущем шаге.")
            return

        try:
            # Разделение аудио на фрагменты
            split_audio(vocals_path, temp_raw_path, 15)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разделить аудио: {str(e)}")
            return

        # Конвертация голоса
        try:
            os.chdir("./sovits")
            from src.audio.audio_conversion import convert
            convert(temp_raw_path, temp_song_path, selected_speaker, noise_scale=0.9, transpose=0)
            os.chdir("../")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить конвертацию голоса: {str(e)}")
            return

        # Объединение обработанного вокала с инструменталом
        try:
            merge(temp_song_path, temp_song_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось объединить аудио: {str(e)}")
            return

        output_path = Path.cwd() / "output"
        output_path.mkdir(exist_ok=True)
        
        final_output_path = output_path / f"{Path(self.separation_window.song_path).stem}_converted.wav"
        
        try:
            shutil.move(str(temp_song_path / "merged.wav"), str(final_output_path))
        except FileNotFoundError:
            QMessageBox.warning(self, "Ошибка", f"Файл {temp_song_path / 'merged.wav'} не найден.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось переместить файл: {str(e)}")
            return

        QMessageBox.information(self, "Готово", f"Обработка завершена. Результат сохранен в {final_output_path}")

        # Очистка временной директории
        shutil.rmtree(temp_dir)

    def get_speakers(self, models_dir):
        speakers = []
        for _, directories, _ in os.walk(models_dir):
            for folder in directories:
                current_speaker = {}
                current_path = Path(models_dir, folder)
                pth_path_template = str(current_path / "G_*.pth")
                pth_paths = glob.glob(pth_path_template)
                if len(pth_paths) == 0:
                    continue
                current_speaker["model_path"] = pth_paths[0]
                current_speaker["model_folder"] = folder

                pt_path_template = str(current_path / "*.pt")
                cluster_models = glob.glob(pt_path_template)
                current_speaker["cluster_path"] = cluster_models[0] if cluster_models else ""

                json_path_template = str(current_path / "*.json")
                configs = glob.glob(json_path_template)
                if len(configs) == 0:
                    continue
                current_speaker["cfg_path"] = configs[0]
                with open(current_speaker["cfg_path"]) as f:
                    try:
                        cfg_json = json.loads(f.read())
                    except Exception as e:
                        continue
                    for name, i in cfg_json["spk"].items():
                        current_speaker["name"] = name
                        current_speaker["id"] = i
                        if not name.startswith('.'):
                            speakers.append(current_speaker)
        return sorted(speakers, key=lambda x: x["name"].lower())

if __name__ == "__main__":
    # Initialize path manager
    path_mgr = PathManager()
    
    # Ensure required directories exist
    required_dirs = ['песни', 'temp', 'models', 'output', 'sovits']
    for dir_name in required_dirs:
        dir_path = path_mgr.get_path(dir_name)
        dir_path.mkdir(exist_ok=True)
    
    # Handle config.json
    config_path = path_mgr.get_path('config.json')
    try:
        with open("config.json", 'r') as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        config_data = {}
        with open('config.json', 'w') as f:
            json.dump(config_data, f)

    if "initial_setup_done" not in config_data or config_data["initial_setup_done"] != "True":
        try:
            src.utils.startup.initial_setup()
            config_data["initial_setup_done"] = "True"
            with open('config.json', 'w') as f:
                json.dump(config_data, f)
        except Exception as e:
            print("an error occured while running startup")
            print(e)
            sys.exit()

    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
