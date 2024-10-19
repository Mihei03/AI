import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog,  QLabel, QPushButton, QComboBox, QProgressBar, QMessageBox, QHBoxLayout, QLineEdit, QCheckBox
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import os
from pathlib import Path
import shutil
import glob
import json
import traceback

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
            from src.audio.audio_conversion import convert
            hubert_model_path = Path("hubert") / "checkpoint_best_legacy_500.pt"
            if not hubert_model_path.exists():
                raise FileNotFoundError(f"Модель hubert не найдена: {hubert_model_path}")
            
            total_files = len(list(self.temp_raw_path.glob('*.wav')))
            for i, file in enumerate(self.temp_raw_path.glob('*.wav')):
                convert(file, self.temp_song_path, self.selected_speaker, hubert_model_path, noise_scale=0.9, transpose=0)
                self.progress.emit(int((i + 1) / total_files * 100))
            self.finished.emit()
        except ImportError as e:
            self.error.emit(f"Ошибка импорта модуля: {str(e)}\n{traceback.format_exc()}")
        except FileNotFoundError as e:
            self.error.emit(f"Файл модели не найден: {str(e)}\n{traceback.format_exc()}")
        except Exception as e:
            self.error.emit(f"Произошла ошибка: {str(e)}\n{traceback.format_exc()}")

class ModelSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_model_path = None

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.model_label = QLabel("Выберите папку с моделью голоса:")
        self.model_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.model_label)

        model_selection_layout = QHBoxLayout()
        self.model_path_label = QLabel("Папка не выбрана")
        self.model_path_label.setStyleSheet("font-size: 14px;")
        model_selection_layout.addWidget(self.model_path_label)

        self.select_model_button = QPushButton("Выбрать модель")
        self.select_model_button.setStyleSheet("font-size: 14px;")
        self.select_model_button.clicked.connect(self.select_model)
        model_selection_layout.addWidget(self.select_model_button)

        layout.addLayout(model_selection_layout)

        layout.addStretch(5)
        self.trans_label = QLabel("Высота тона (хороший диапазон от -12 до 12):")
        self.trans_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.trans_label)
        self.trans_tx = QLineEdit()
        self.trans_tx.setStyleSheet("font-size: 16px;")
        self.trans_tx.setText("0")
        layout.addWidget(self.trans_tx)

        layout.addStretch(5)
        self.cluster_ratio_label = QLabel("Соотношение между звучанием, похожим на тембр цели, \nчеткостью и артикулированностью:")
        layout.addWidget(self.cluster_ratio_label)
        self.cluster_ratio_label.setStyleSheet("font-size: 16px;")
        self.cluster_ratio_tx = QLineEdit()
        self.cluster_ratio_tx.setStyleSheet("font-size: 16px;")
        self.cluster_ratio_tx.setText("0.0")
        layout.addWidget(self.cluster_ratio_tx)

        layout.addStretch(5)
        self.noise_scale_label = QLabel("Если выходной сигнал звучит гулко, попробуйте увеличить масштаб шума:")
        layout.addWidget(self.noise_scale_label)
        self.noise_scale_label.setStyleSheet("font-size: 16px;")
        self.noise_scale_tx = QLineEdit()
        self.noise_scale_tx.setStyleSheet("font-size: 16px;")
        self.noise_scale_tx.setText("0.4")
        layout.addWidget(self.noise_scale_tx)

        layout.addStretch(5)
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Назад")
        self.back_button.setStyleSheet("font-size: 16px;")
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        self.next_button = QPushButton("Далее")
        self.next_button.setStyleSheet("font-size: 16px;")
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def select_model(self):
        initial_dir = str(Path.cwd() / "src" / "SOVITS" / "models")
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с моделью", initial_dir)
        
        if folder_path:
            if self.check_model_folder(folder_path):
                self.selected_model_path = folder_path
                self.model_path_label.setText(f"Выбрана папка: {os.path.basename(folder_path)}")
            else:
                QMessageBox.warning(self, "Ошибка", "В выбранной папке не найдены необходимые файлы (.json и .pth)")
    
    def check_model_folder(self, folder_path):
        json_files = glob.glob(os.path.join(folder_path, "*.json"))
        pth_files = glob.glob(os.path.join(folder_path, "*.pth"))
        return len(json_files) > 0 and len(pth_files) > 0
    
    def get_selected_speaker(self):
        if not self.selected_model_path:
            return None

        speaker = {}
        json_files = glob.glob(os.path.join(self.selected_model_path, "*.json"))
        pth_files = glob.glob(os.path.join(self.selected_model_path, "G_*.pth"))
        pt_files = glob.glob(os.path.join(self.selected_model_path, "*.pt"))

        if json_files and pth_files:
            speaker["cfg_path"] = json_files[0]
            speaker["model_path"] = pth_files[0]
            speaker["cluster_path"] = pt_files[0] if pt_files else ""
            speaker["model_folder"] = os.path.basename(self.selected_model_path)

            with open(speaker["cfg_path"]) as f:
                try:
                    cfg_json = json.load(f)
                    for name, i in cfg_json["spk"].items():
                        speaker["name"] = name
                        speaker["id"] = i
                        break
                except Exception:
                    return None

            return speaker
        
        return None
    
    def populate_models(self, models):
        self.model_combobox.clear()
        for model in models:
            self.model_combobox.addItem(model["name"])

    def process_model_selection(self, temp_dir, song_path):
        selected_model = self.model_combobox.currentText()
        selected_speaker = next((s for s in self.get_speakers(Path.cwd() / "SOVITS" / "models") if s["name"] == selected_model), None)
        
        if not selected_speaker:
            QMessageBox.warning(self, "Ошибка", "Выбранная модель не найдена.")
            return

        temp_song_path = Path("SOVITS") / "temp" / Path(song_path).stem
        temp_raw_path = temp_song_path / "raw"
        temp_raw_path.mkdir(parents=True, exist_ok=True)

        try:
            split_audio(temp_song_path / "vocals.wav", temp_raw_path, 15)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разделить аудио: {str(e)}")
            return

        transpose = int(self.trans_tx.text())
        cluster_ratio = float(self.cluster_ratio_tx.text())
        noise_scale = float(self.noise_scale_tx.text())

        try:
            from src.audio.audio_conversion import convert
            hubert_model_path = Path("hubert") / "checkpoint_best_legacy_500.pt"
            if not hubert_model_path.exists():
                raise FileNotFoundError(f"Модель hubert не найдена: {hubert_model_path}")
            
            convert(temp_raw_path, temp_song_path, selected_speaker, noise_scale=noise_scale, transpose=transpose, cluster_ratio=cluster_ratio)
            
            # После конвертации возвращаем управление в MainApp
            self.parent().show_audio_processing_window(temp_song_path)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при конвертации: {str(e)}")
            return None

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_error(self, error_message):
        QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при конвертации: {error_message}")
        self.next_button.setEnabled(True)
        self.back_button.setEnabled(True)

    def finish_conversion(self):
        temp_song_path = self.worker.temp_song_path
        
        try:
            output_path = Path.cwd() / "SOVITS" / "output"
            output_path.mkdir(exist_ok=True)
            
            # Проверяем наличие файла output.wav
            if (temp_song_path / "output.wav").exists():
                final_output_path = output_path / f"{temp_song_path.stem}_converted.wav"
                shutil.move(str(temp_song_path / "output.wav"), str(final_output_path))
                QMessageBox.information(self, "Готово", "Обработка завершена успешно. Переходим к слиянию песен.")
                self.parent().show_audio_processing_window(temp_song_path)  # Переход к окну слияния песен
            else:
                # Если output.wav не найден, выводим сообщение об ошибке
                raise FileNotFoundError(f"Файл output.wav не найден в {temp_song_path}")

        except FileNotFoundError as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла неожиданная ошибка: {str(e)}\n{traceback.format_exc()}")
        finally:
            # Разблокируем кнопки после завершения
            self.next_button.setEnabled(True)
            self.back_button.setEnabled(True)

    def get_speakers(self, models_dir):
        # Ваш существующий код для get_speakers
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