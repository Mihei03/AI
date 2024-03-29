import copy
import glob
import io
import json
import logging
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QLabel, QLineEdit, QCheckBox, QPushButton, QFileDialog
import sovits.converter as converter

from model_loader import download

CURRENT_DIR = os.path.dirname(__file__)
SOVITS_DIR = f"{CURRENT_DIR}/sovits"
MODELS_DIR = f"{SOVITS_DIR}/models"


def get_speakers(models_dir):
    speakers = []
    for _, dirs, _ in os.walk(models_dir):
        for folder in dirs:
            # ... (код для получения информации о модели)
            cur_speaker = {}
            # Ищем G_****.pth
            g = glob.glob(os.path.join(models_dir, folder, 'G_*.pth'))
            if not len(g):
                print("Skipping " + folder + ", no G_*.pth")
                continue
            cur_speaker["model_path"] = g[0]
            cur_speaker["model_folder"] = folder

            # Ищем *.pt (модель кластеризации)
            clst = glob.glob(os.path.join(models_dir, folder, '*.pt'))
            if not len(clst):
                print("Note: No clustering model found for " + folder)
                cur_speaker["cluster_path"] = ""
            else:
                cur_speaker["cluster_path"] = clst[0]

            # Ищем config.json
            cfg = glob.glob(os.path.join(models_dir, folder, '*.json'))
            if not len(cfg):
                print("Skipping " + folder + ", no config json")
                continue
            cur_speaker["cfg_path"] = cfg[0]
            with open(cur_speaker["cfg_path"]) as f:
                try:
                    cfg_json = json.loads(f.read())
                except Exception as e:
                    print("Malformed config json in " + folder)
                for name, i in cfg_json["spk"].items():
                    cur_speaker["name"] = name
                    cur_speaker["id"] = i
                    if not name.startswith('.'):
                        speakers.append(copy.copy(cur_speaker))

    return sorted(speakers, key=lambda x:x["name"].lower())


class InferenceGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inference GUI")

        download(["https://huggingface.co/therealvul/so-vits-svc-4.0-init/resolve/main/checkpoint_best_legacy_500.pt"], filenames=[f"{SOVITS_DIR}/hubert/checkpoint_best_legacy_500.pt"])
        model_url = "https://mega.nz/file/Dr40kCQI#G3bEWPvUvTa9SBJKQt7rETgcFds4ssnJF0nGN9aAXTk"
        download([model_url])

        logging.getLogger('numba').setLevel(logging.WARNING)
        self.existing_files = []
        self.slice_db = -40
        self.wav_format = 'wav'

        self.models_dir = MODELS_DIR
        self.speakers = get_speakers(self.models_dir)
        
        # Создание виджетов GUI (комбобокс, поля ввода, кнопки и т.д.)
        self.input_path_btn = QPushButton("Выбрать путь к входной песне")
        self.input_path_btn.clicked.connect(self.select_input_path)
        self.input_path_label = QLabel("Путь к входной песне:")
        self.input_path_tx = QLineEdit()
        self.input_path_tx.setText(os.path.join(os.path.expanduser("~"), "Desktop"))
        self.input_path_tx.setReadOnly(True)
        
        self.model_path_btn = QPushButton("Выбрать путь к моделям")
        self.model_path_btn.clicked.connect(self.select_model_path)
        self.model_path_label = QLabel("Путь к моделям:")
        self.model_path_tx = QLineEdit()
        self.model_path_tx.setText(self.models_dir)
        self.model_path_btn.setEnabled(False)  # Изначально кнопка выбора пути к моделям заблокирована
        self.model_path_tx.setReadOnly(True)
        
        self.speaker_label = QLabel("Модели голоса:")
        self.speaker_box = QComboBox()
        self.speaker_box.setEnabled(False)  # Изначально комбобокс выбора модели голоса заблокирован
        
        self.trans_label = QLabel("Высота тона (хороший диапазон от -12 до 12):")
        self.trans_tx = QLineEdit()
        self.trans_tx.setText("0")
        self.trans_tx.setEnabled(False)  # Изначально поле ввода высоты тона заблокировано
        
        self.cluster_ratio_label = QLabel("Соотношение между звучанием, похожим на тембр цели, \nчеткостью и артикулированностью, чтобы найти подходящий компромисс:")
        self.cluster_ratio_tx = QLineEdit()
        self.cluster_ratio_tx.setText("0.0")
        self.cluster_ratio_tx.setEnabled(False)  # Изначально поле ввода соотношения кластеров заблокировано
        
        self.noise_scale_label = QLabel("Если выходной сигнал звучит гулко, попробуйте увеличить масштаб шума:")
        self.noise_scale_tx = QLineEdit()
        self.noise_scale_tx.setText("0.4")
        self.noise_scale_tx.setEnabled(False)  # Изначально поле ввода масштаба шума заблокировано
        
        self.auto_pitch_ck = QCheckBox("Автоматическое предсказание высоты тона. \nОставьте этот флажок не отмеченным, если вы конвертируете певческий голос.")
        self.auto_pitch_ck.setEnabled(False)  # Изначально чекбокс автоматического предсказания высоты тона заблокирован
        
        self.save_path_btn = QPushButton("Выбрать путь сохранения")
        self.save_path_btn.clicked.connect(self.select_save_path)
        self.save_path_label = QLabel("Путь сохранения:")
        self.save_path_tx = QLineEdit()
        self.save_path_tx.setText(os.path.join(os.path.expanduser("~"), "Desktop"))
        self.save_path_btn.setEnabled(False)  # Изначально кнопка выбора пути сохранения заблокирована
        self.save_path_tx.setReadOnly(True)
        
        self.convert_btn = QPushButton("Конвертировать")
        self.convert_btn.clicked.connect(self.convert)
        self.convert_btn.setEnabled(False)  # Изначально кнопка конвертировать заблокирована
        
        self.clean_btn = QPushButton("Удалить все аудиофайлы")
        self.clean_btn.clicked.connect(self.clean)
        self.clean_btn.setEnabled(False)  # Изначально кнопка удаления аудиофайлов заблокирована
        
        # Создание макета и центрального виджета
        layout = QVBoxLayout()
        layout.addWidget(self.input_path_label)
        layout.addWidget(self.input_path_tx)
        layout.addWidget(self.input_path_btn)
        layout.addWidget(self.model_path_label)
        layout.addWidget(self.model_path_tx)
        layout.addWidget(self.model_path_btn)
        layout.addWidget(self.speaker_label)
        layout.addWidget(self.speaker_box)
        layout.addWidget(self.trans_label)
        layout.addWidget(self.trans_tx)
        layout.addWidget(self.cluster_ratio_label)
        layout.addWidget(self.cluster_ratio_tx)
        layout.addWidget(self.noise_scale_label)
        layout.addWidget(self.noise_scale_tx)
        layout.addWidget(self.auto_pitch_ck)
        layout.addWidget(self.save_path_label)
        layout.addWidget(self.save_path_tx)
        layout.addWidget(self.save_path_btn)
        layout.addWidget(self.convert_btn)
        layout.addWidget(self.clean_btn)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Обновляем список моделей голоса после создания всех виджетов
        self.update_speaker_box()

    def select_input_path(self):
        input_path = QFileDialog.getOpenFileName(self, "Выбрать входную песню", filter="Audio Files (*.wav *.flac *.mp3 *.ogg *.opus)")
        if input_path[0]:
            self.input_path_tx.setText(input_path[0])
            self.model_path_btn.setEnabled(True)  # После выбора входной песни разблокируем кнопку выбора пути к моделям
            
    def select_model_path(self):
        model_path = QFileDialog.getExistingDirectory(self, "Выбрать путь к моделям")
        if model_path:
            self.model_path_tx.setText(model_path)
            self.update_speaker_box()
            self.speaker_box.setEnabled(True)  # После выбора пути к моделям разблокируем комбобокс выбора модели голоса

    def select_model_path(self):
        model_path = QFileDialog.getExistingDirectory(self, "Выбрать путь к моделям")
        if model_path:
            self.model_path_tx.setText(model_path)
            self.update_speaker_box()
            self.speaker_box.setEnabled(True)
            self.trans_tx.setEnabled(True)
            self.cluster_ratio_tx.setEnabled(True)
            self.noise_scale_tx.setEnabled(True)
            self.auto_pitch_ck.setEnabled(True)
            self.save_path_btn.setEnabled(True)
        
    def update_speaker_box(self):
        self.speaker_box.clear()
        self.speakers = get_speakers(self.model_path_tx.text())
        self.speaker_box.addItems([x["name"] for x in self.speakers])
        
    def select_save_path(self):
        save_path = QFileDialog.getExistingDirectory(self, "Выбрать путь сохранения")
        if save_path:
            self.save_path_tx.setText(save_path)
            self.convert_btn.setEnabled(True)
            self.clean_btn.setEnabled(True) 
            
    # Функция для преобразования аудиофайлов
    def convert(self):
        os.chdir(f"{os.getcwd()}/sovits")
        result = converter.convert(self.input_path_tx.text(), 
                          self.trans_tx.text(),
                          self.speakers,
                          self.speaker_box.currentText(),
                          self.cluster_ratio_tx.text(),
                          self.auto_pitch_ck.isChecked(),
                          self.noise_scale_tx.text(),
                          self.save_path_tx.text(),
                          self.slice_db)
        self.clean_btn.setEnabled(result)
        os.chdir(os.pardir)
            
    # Функция для удаления аудиофайлов
    def clean(self):
        input_filepaths = [f for f in glob.glob(os.path.join(self.save_path_tx.text(), '*.*'), recursive=True)
                            if f not in self.existing_files and
                            any(f.endswith(ex) for ex in ['.wav', '.flac', '.mp3', '.ogg', '.opus'])]
        for f in input_filepaths:
            os.remove(f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    inference_gui = InferenceGui()
    inference_gui.show()
    sys.exit(app.exec_())