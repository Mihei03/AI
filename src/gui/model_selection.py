import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QProgressBar, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import os
from pathlib import Path
import shutil
import glob
import json

project_root = Path(__file__).parent
sys.path.append(str(project_root))

import copy
import glob
import os
import json

from src.audio.audio_separation import split_audio
from src.audio.audio_merging import merge

class ConversionWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, temp_raw_path, temp_song_path, selected_speaker):
        super().__init__()
        self.temp_raw_path = temp_raw_path
        self.temp_song_path = temp_song_path
        self.selected_speaker = selected_speaker

    def run(self):
        try:
            os.chdir("./sovits")
            from src.audio.audio_conversion import convert
            total_files = len(list(self.temp_raw_path.glob('*.wav')))
            for i, file in enumerate(self.temp_raw_path.glob('*.wav')):
                convert(file, self.temp_song_path, self.selected_speaker, noise_scale=0.9, transpose=0)
                self.progress.emit(int((i + 1) / total_files * 100))
            os.chdir("../")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ModelSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = None
        self.worker = None

    def initUI(self):
        layout = QVBoxLayout()

        self.model_label = QLabel("Выберите модель голоса:")
        layout.addWidget(self.model_label)

        self.model_combobox = QComboBox()
        layout.addWidget(self.model_combobox)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Назад")
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        self.next_button = QPushButton("Далее")
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def populate_models(self, models):
        self.model_combobox.clear()
        for model in models:
            self.model_combobox.addItem(model["name"])

    def process_model_selection(self, temp_dir, song_path):
        selected_model = self.model_combobox.currentText()
        selected_speaker = next((s for s in self.get_speakers(Path.cwd() / "models") if s["name"] == selected_model), None)
        
        if not selected_speaker:
            QMessageBox.warning(self, "Ошибка", "Выбранная модель не найдена.")
            return

        temp_song_path = temp_dir / Path(song_path).stem
        temp_raw_path = temp_song_path / "raw"

        # Убедимся, что папка raw существует
        temp_raw_path.mkdir(parents=True, exist_ok=True)

        # Разделение аудио на фрагменты
        try:
            split_audio(temp_song_path / "vocals.wav", temp_raw_path, 15)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разделить аудио: {str(e)}")
            return

        # Конвертация голоса
        self.thread = QThread()
        self.worker = ConversionWorker(temp_raw_path, temp_song_path, selected_speaker)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.finish_conversion)
        self.worker.error.connect(self.show_error)

        # Блокируем кнопки во время конвертации
        self.next_button.setEnabled(False)
        self.back_button.setEnabled(False)

        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_error(self, error_message):
        QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при конвертации: {error_message}")
        self.next_button.setEnabled(True)
        self.back_button.setEnabled(True)

    def finish_conversion(self):
        temp_song_path = self.worker.temp_song_path
        
        try:
            # Объединение обработанного вокала с инструменталом
            merge(temp_song_path, temp_song_path)

            output_path = Path.cwd() / "output"
            output_path.mkdir(exist_ok=True)
            
            final_output_path = output_path / f"{temp_song_path.stem}_converted.wav"
            
            # Проверяем наличие файла output.wav
            if (temp_song_path / "merged.wav").exists():
                shutil.move(str(temp_song_path / "merged.wav"), str(final_output_path))
            else:
                # Если output.wav не найден, пробуем объединить vocals.wav с другими треками
                self.merge_tracks(temp_song_path, final_output_path)

            QMessageBox.information(self, "Готово", f"Обработка завершена. Результат сохранен в {final_output_path}")

            # Очистка временной директории
            shutil.rmtree(temp_song_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при завершении конвертации: {str(e)}")
        finally:
            # Разблокируем кнопки после завершения
            self.next_button.setEnabled(True)
            self.back_button.setEnabled(True)

    def merge_tracks(self, temp_song_path, final_output_path):
        from pydub import AudioSegment

        vocals = AudioSegment.from_wav(str(temp_song_path / "vocals.wav"))
        
        other_tracks = []
        for track in ["bass.wav", "drums.wav", "other.wav", "piano.wav"]:
            if (temp_song_path / track).exists():
                other_tracks.append(AudioSegment.from_wav(str(temp_song_path / track)))

        merged = vocals
        for track in other_tracks:
            merged = merged.overlay(track)

        merged.export(str(final_output_path), format="wav")

    def get_speakers(self, models_dir):
        # Ваш существующий код для get_speakers
        speakers = []
        for _, directories, _ in os.walk(models_dir):
            for folder in directories:
                current_speaker = {}
                current_path = Path(models_dir, folder)
                pth_path_template = str(current_path / "G_*.pth")
                pth_paths = glob.glob(pth_path_template)
                if len(pth_paths == 0):
                    continue
                current_speaker["model_path"] = pth_paths[0]
                current_speaker["model_folder"] = folder

                pt_path_template = str(current_path / "*.pt")
                cluster_models = glob.glob(pt_path_template)
                current_speaker["cluster_path"] = cluster_models[0] if cluster_models else ""

                json_path_template = str(current_path / "*.json")
                configs = glob.glob(json_path_template)
                if len(configs == 0):
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