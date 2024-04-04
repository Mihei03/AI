import os
import sys
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow, QCheckBox, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
import random
import json
import pathlib
import subprocess

class TrainThread(QThread):
    update_log = pyqtSignal(str)

    def __init__(self, exp_dir1, sr2, if_f0_3, spk_id5, save_epoch10, total_epoch11, batch_size12, if_save_latest13, pretrained_G14, pretrained_D15, gpus16, if_cache_gpu17, if_save_every_weights18, version19):
        super().__init__()
        self.exp_dir1 = exp_dir1
        self.sr2 = sr2
        self.if_f0_3 = if_f0_3
        self.spk_id5 = spk_id5
        self.save_epoch10 = save_epoch10
        self.total_epoch11 = total_epoch11
        self.batch_size12 = batch_size12
        self.if_save_latest13 = if_save_latest13
        self.pretrained_G14 = pretrained_G14
        self.pretrained_D15 = pretrained_D15
        self.gpus16 = gpus16
        self.if_cache_gpu17 = if_cache_gpu17
        self.if_save_every_weights18 = if_save_every_weights18
        self.version19 = version19

    def run(self):
        log = click_train(self.exp_dir1, self.sr2, self.if_f0_3, self.spk_id5, self.save_epoch10, self.total_epoch11, self.batch_size12, self.if_save_latest13, self.pretrained_G14, self.pretrained_D15, self.gpus16, self.if_cache_gpu17, self.if_save_every_weights18, self.version19)
        self.update_log.emit(log)

def click_train(exp_dir1, sr2, if_f0_3, spk_id5, save_epoch10, total_epoch11, batch_size12, if_save_latest13, pretrained_G14, pretrained_D15, gpus16, if_cache_gpu17, if_save_every_weights18, version19):
    now_dir = os.getcwd()

    # Генерация filelist
    exp_dir = f"{now_dir}/logs/{exp_dir1}"
    os.makedirs(exp_dir, exist_ok=True)
    gt_wavs_dir = f"{exp_dir}/0_gt_wavs"
    feature_dir = f"{exp_dir}/3_feature{768 if version19 == 'v2' else 256}"
    if if_f0_3:
        f0_dir = f"{exp_dir}/2a_f0"
        f0nsf_dir = f"{exp_dir}/2b-f0nsf"
        names = (
            set([name.split(".")[0] for name in os.listdir(gt_wavs_dir)])
            & set([name.split(".")[0] for name in os.listdir(feature_dir)])
            & set([name.split(".")[0] for name in os.listdir(f0_dir)])
            & set([name.split(".")[0] for name in os.listdir(f0nsf_dir)])
        )
    else:
        names = set([name.split(".")[0] for name in os.listdir(gt_wavs_dir)]) & set([name.split(".")[0] for name in os.listdir(feature_dir)])
    opt = []
    for name in names:
        if if_f0_3:
            opt.append(
                f"{gt_wavs_dir}/{name}.wav|{feature_dir}/{name}.npy|{f0_dir}/{name}.wav.npy|{f0nsf_dir}/{name}.wav.npy|{spk_id5}"
            )
        else:
            opt.append(
                f"{gt_wavs_dir}/{name}.wav|{feature_dir}/{name}.npy|{spk_id5}"
            )
    fea_dim = 768 if version19 == "v2" else 256
    if if_f0_3:
        for _ in range(2):
            opt.append(
                f"{now_dir}/logs/mute/0_gt_wavs/mute{sr2}.wav|{now_dir}/logs/mute/3_feature{fea_dim}/mute.npy|{now_dir}/logs/mute/2a_f0/mute.wav.npy|{now_dir}/logs/mute/2b-f0nsf/mute.wav.npy|{spk_id5}"
            )
    else:
        for _ in range(2):
            opt.append(
                f"{now_dir}/logs/mute/0_gt_wavs/mute{sr2}.wav|{now_dir}/logs/mute/3_feature{fea_dim}/mute.npy|{spk_id5}"
            )
    random.shuffle(opt)
    with open(f"{exp_dir}/filelist.txt", "w") as f:
        f.write("\n".join(opt))

    print("Запись списка файлов завершена")
    print(f"Использование графических процессоров: {gpus16}")
    if pretrained_G14 == "":
        print("Нет предварительно обученного генератора")
    if pretrained_D15 == "":
        print("Без предварительно обученного дискриминатора")
    if version19 == "v1" or sr2 == "40k":
        config_path = f"configs/v1/{sr2}.json"
    else:
        config_path = f"configs/v2/{sr2}.json"
    config_save_path = os.path.join(exp_dir, "config.json")
    if not pathlib.Path(config_save_path).exists():
        with open(config_save_path, "w", encoding="utf-8") as f:
            with open(config_path, "r") as config_file:
                config_data = json.load(config_file)
                json.dump(config_data, f, ensure_ascii=False, indent=4, sort_keys=True)
            f.write("\n")

    cmd = (
        f'python C:/Users/mihei/Desktop/RVC/TrainVocModel/infer/modules/train/train.py -e "{exp_dir1}" -sr {sr2} -f0 {"1" if if_f0_3 else "0"} -bs {batch_size12} -g {gpus16} -te {total_epoch11} -se {save_epoch10} {"" if pretrained_G14 == "" else f"-pg {pretrained_G14}"} {"" if pretrained_D15 == "" else f"-pd {pretrained_D15}"} -l {"1" if if_save_latest13 else "0"} -c {"1" if if_cache_gpu17 else "0"} -sw {"1" if if_save_every_weights18 else "0"} -v {version19}'
    )

    process = subprocess.Popen(cmd, shell=True, cwd=now_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    output = []
    while True:
        line = process.stdout.readline()
        if not line:
            break
        output.append(line.strip())
        print(line.strip())

    process.wait()
    return "Обучение завершено, вы можете просмотреть журнал обучения в консоли или файле train.log в папке эксперимента"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Тренировка модели")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        layout = QVBoxLayout()

        self.save_frequency_input = QLineEdit()
        self.save_frequency_input.setPlaceholderText("Введите частоту сохранения модели")
        layout.addWidget(QLabel("Частота сохранения модели:"))
        layout.addWidget(self.save_frequency_input)

        self.epochs_input = QLineEdit()
        self.epochs_input.setPlaceholderText("Введите количество эпох")
        layout.addWidget(QLabel("Количество эпох:"))
        layout.addWidget(self.epochs_input)

        self.batch_size_input = QLineEdit()
        self.batch_size_input.setPlaceholderText("Введите размер батча")
        layout.addWidget(QLabel("Размер батча:"))
        layout.addWidget(self.batch_size_input)

        self.cache_checkbox = QCheckBox("Использовать кэш GPU")
        layout.addWidget(self.cache_checkbox)

        layout.addWidget(QLabel("Выберите модель:"))
        self.model_combo_box = QComboBox()
        self.model_combo_box.addItems([
            "Default ( 32k / 40k / 48k )",
            "Ov2Super - Для Иностранных моделей ( 40k )",
            "RIN_E3 - Для Иностранных моделей ( 40k )",
            "Snowie v2 - Для Русских моделей ( 40k / 48k )",
            "Snowie v3 - Для Русских моделей ( 32k / 40k / 48k )",
            "Snowie v3 + RIN_E3 - Для Русских моделей ( 40k )"
        ])
        layout.addWidget(self.model_combo_box)

        self.log_label = QLabel()
        layout.addWidget(self.log_label)

        train_button = QPushButton("Начать обучение")
        train_button.clicked.connect(self.start_training)
        layout.addWidget(train_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_training(self):
        selected_model = self.model_combo_box.currentText()
        save_frequency = int(self.save_frequency_input.text() or "20")
        epochs = int(self.epochs_input.text() or "500")
        batch_size = int(self.batch_size_input.text() or "7")
        cache = self.cache_checkbox.isChecked()
        sample_rate = "32000"
        if selected_model == "Default ( 32k / 40k / 48k )":
            # Устанавливаем частоту дискретизации или другие параметры специфичные для модели
            sample_rate = "32000"  # Пример, реальное значение зависит от вашей логики

        # Здесь вы можете добавить код для получения других параметров, таких как имя модели, частота дискретизации и т.д.

        self.train_thread = TrainThread(
            exp_dir1="MiHei",
            sr2=sample_rate,
            if_f0_3=True,
            spk_id5=0,
            save_epoch10=save_frequency,
            total_epoch11=epochs,
            batch_size12=batch_size,
            if_save_latest13=True,
            pretrained_G14="",
            pretrained_D15="",
            gpus16=0,
            if_cache_gpu17=cache,
            if_save_every_weights18=True,
            version19="v2",
        )
        self.train_thread.update_log.connect(self.log_label.setText)
        self.train_thread.start()
        sample_rate = "32000"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())