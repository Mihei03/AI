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

    def show_welcome_window(self):
        self.welcome_window = WelcomeWindow()

        # Обработчики для кнопок
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
        self.model_selection_window.populate_models(self.get_speakers(self.path_mgr.get_path("models")))
        self.model_selection_window.back_button.clicked.connect(self.show_separation_window)
        self.model_selection_window.next_button.clicked.connect(self.process_model_selection)
        self.setCentralWidget(self.model_selection_window)

    def process_audio(self):
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
        selected_model = self.model_selection_window.model_combobox.currentText()
        selected_speaker = next((s for s in self.get_speakers(self.path_mgr.get_path("models")) if s["name"] == selected_model), None)
        
        if not selected_speaker:
            QMessageBox.warning(self, "Ошибка", "Выбранная модель не найдена.")
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
            print(f"Current working directory: {os.getcwd()}")
            print(f"SOVITS directory: {self.path_mgr.sovits_dir}")
            print(f"Files in SOVITS directory: {os.listdir(self.path_mgr.sovits_dir)}")
            
            # Добавляем путь к директории so-vits-svc-eff-4.0
            #sovits_path = self.path_mgr.get_path("so-vits-svc-eff-4.0")
            #sys.path.append(str(sovits_path))
            
            os.chdir(str(self.path_mgr.sovits_dir))  # Меняем текущую директорию
            from src.audio.audio_conversion import convert
            transpose = int(self.model_selection_window.trans_tx.text())
            cluster_ratio = float(self.model_selection_window.cluster_ratio_tx.text())
            noise_scale = float(self.model_selection_window.noise_scale_tx.text())
            #auto_pitch = self.model_selection_window.auto_pitch_ck.isChecked()
            convert(temp_raw_path, temp_song_path, selected_speaker, noise_scale=noise_scale, transpose=transpose, cluster_ratio=cluster_ratio)
            os.chdir(str(self.path_mgr.ai_code_dir))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить конвертацию голоса: {str(e)}")
            return

        try:
            merge(temp_song_path, temp_song_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось объединить аудио: {str(e)}")
            return

        output_path = self.path_mgr.get_path("output")
        output_path.mkdir(exist_ok=True)
        
        final_output_path = output_path / f"{Path(self.separation_window.song_path).stem}_converted.wav"
        
        try:
            shutil.move(str(temp_song_path / "output.wav"), str(final_output_path))
        except FileNotFoundError:
            QMessageBox.warning(self, "Ошибка", f"Файл {temp_song_path / 'output.wav'} не найден.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось переместить файл: {str(e)}")
            return

        QMessageBox.information(self, "Готово", f"Обработка завершена. Результат сохранен в {final_output_path}")

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
                        cfg_json = json.load(f)
                    except Exception as e:
                        continue
                    for name, i in cfg_json["spk"].items():
                        current_speaker["name"] = name
                        current_speaker["id"] = i
                        if not name.startswith('.'):
                            speakers.append(current_speaker)
        return sorted(speakers, key=lambda x: x["name"].lower())

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
