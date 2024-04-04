import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QLineEdit, QComboBox, QVBoxLayout, QWidget, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import faiss

class PreprocessThread(QThread):
    update_log = pyqtSignal(str)

    def __init__(self, dataset_folder, sr, model_name):
        super().__init__()
        self.dataset_folder = dataset_folder
        self.sr = sr
        self.model_name = model_name

    def run(self):
        os.makedirs(f'./logs/{self.model_name}', exist_ok=True)
        with open(f'./logs/{self.model_name}/preprocess.log', 'w') as f:
            print("Обрабатываем датасет...", file=f)
        cmd = f'python C:/Users/mihei/Desktop/RVC/TrainVocModel/infer/modules/train/preprocess.py "{self.dataset_folder}" {self.sr} 2 "./logs/{self.model_name}" False 3.0'
        result = os.popen(cmd).read()
        with open(f'./logs/{self.model_name}/preprocess.log', 'r') as f:
            if 'end preprocess' in f.read():
                self.update_log.emit('Предварительная обработка данных завершена.')
            else:
                self.update_log.emit('Ошибка предварительной обработки данных... Убедитесь, что папка с набором данных выбрана правильно.')

class ExtractThread(QThread):
    update_log = pyqtSignal(str)

    def __init__(self, f0method, model_name):
        super().__init__()
        self.f0method = f0method
        self.model_name = model_name

    def run(self):
        with open(f'./logs/{self.model_name}/extract_f0_feature.log', 'w') as f:
            print("Запуск обработки...", file=f)
        if self.f0method == "rmvpe_gpu":
            cmd = f'python C:/Users/mihei/Desktop/RVC/TrainVocModel/infer/modules/train/extract/extract_f0_print.py 1 0 0 "./logs/{self.model_name}" True'
            os.system(cmd)
        else:
            cmd = f'python C:/Users/mihei/Desktop/RVC/TrainVocModel/infer/modules/train/extract/extract_f0_print.py "./logs/{self.model_name}" 2 {self.f0method}'
            os.system(cmd)
        cmd = f'python C:/Users/mihei/Desktop/RVC/TrainVocModel/infer/modules/train/extract_feature_print.py cuda:0 1 0 "./logs/{self.model_name}" v2 True'
        os.system(cmd)
        with open(f'./logs/{self.model_name}/extract_f0_feature.log', 'r') as f:
            if 'all-feature-done' in f.read():
                self.update_log.emit('Извлечение признаков завершено.')
            else:
                self.update_log.emit('Ошибка извлечения признаков... Убедитесь, что папка с набором данных выбрана правильно.')

class TrainIndexThread(QThread):
    update_log = pyqtSignal(str)

    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name

    def run(self):
        logs = train_index(self.model_name, 'v2')
        for log in logs:
            self.update_log.emit(log)

def train_index(exp_dir1, version19):
    exp_dir = f"C:/Users/mihei/Desktop/RVC/logs/{exp_dir1}"
    os.makedirs(exp_dir, exist_ok=True)
    feature_dir = f"{exp_dir}/3_feature768" if version19 == "v2" else f"{exp_dir}/3_feature256"
    if not os.path.exists(feature_dir):
        return ["Пожалуйста, сначала выполните извлечение признаков!"]
    listdir_res = os.listdir(feature_dir)
    if len(listdir_res) == 0:
        return ["Пожалуйста, сначала выполните извлечение признаков!"]
    infos = []
    npys = []
    for name in sorted(listdir_res):
        phone = np.load(f"{feature_dir}/{name}")
        npys.append(phone)
    big_npy = np.concatenate(npys, 0)
    big_npy_idx = np.arange(big_npy.shape[0])
    np.random.shuffle(big_npy_idx)
    big_npy = big_npy[big_npy_idx]
    if big_npy.shape[0] > 2e5:
        infos.append(f"Попытка выполнения kmeans {big_npy.shape[0]} формы до 10к центров.")
        yield "\n".join(infos)
        try:
            from sklearn.cluster import MiniBatchKMeans
            from TrainVocModel.configs import config
            big_npy = MiniBatchKMeans(
                n_clusters=10000,
                verbose=True,
                batch_size=256 * config.n_cpu,
                compute_labels=False,
                init="random",
            ).fit(big_npy).cluster_centers_
        except Exception as e:
            info = str(e)
            infos.append(info)
            yield "\n".join(infos)

    np.save(f"{exp_dir}/total_fea.npy", big_npy)
    n_ivf = min(int(16 * np.sqrt(big_npy.shape[0])), big_npy.shape[0] // 39)
    infos.append(f"{big_npy.shape},{n_ivf}")
    yield "\n".join(infos)
    index = faiss.index_factory(768 if version19 == "v2" else 256, f"IVF{n_ivf},Flat")
    infos.append("обучение")
    yield "\n".join(infos)
    index_ivf = faiss.extract_index_ivf(index)
    index_ivf.nprobe = 1
    index.train(big_npy)
    faiss.write_index(
        index,
        f"{exp_dir}/trained_IVF{n_ivf}_Flat_nprobe_{index_ivf.nprobe}_{exp_dir1}_{version19}.index"
    )

    infos.append("добавление")
    yield "\n".join(infos)
    batch_size_add = 8192
    for i in range(0, big_npy.shape[0], batch_size_add):
        index.add(big_npy[i:i+batch_size_add])
        infos.append(f"Добавлено {i+batch_size_add} / {big_npy.shape[0]}")
        yield "\n".join(infos)

    faiss.write_index(index, f"{exp_dir}/final_{exp_dir1}_{version19}.index")
    infos.append("Индекс создан")
    yield "\n".join(infos)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create widgets
        dataset_label = QLabel("Выберите папку с набором данных:")
        self.dataset_folder_line_edit = QLineEdit()
        dataset_folder_button = QPushButton("Обзор")
        dataset_folder_button.clicked.connect(self.select_dataset_folder)

        sr_label = QLabel("Частота дискретизации:")
        self.sr_combo_box = QComboBox()
        self.sr_combo_box.addItems(["32k", "40k", "48k"])

        model_name_label = QLabel("Имя модели:")
        self.model_name_line_edit = QLineEdit()

        f0method_label = QLabel("Метод извлечения F0:")
        self.f0method_combo_box = QComboBox()
        self.f0method_combo_box.addItems(["rmvpe_gpu", "pm", "pm2", "harvest"])

        preprocess_button = QPushButton("Предварительная обработка")
        preprocess_button.clicked.connect(self.start_preprocess)

        extract_button = QPushButton("Извлечь признаки")
        extract_button.clicked.connect(self.start_extract)

        train_index_button = QPushButton("Обучить индекс")
        train_index_button.clicked.connect(self.start_train_index)

        self.log_label = QLabel()

        # Layout widgets
        dataset_folder_layout = QHBoxLayout()
        dataset_folder_layout.addWidget(self.dataset_folder_line_edit)
        dataset_folder_layout.addWidget(dataset_folder_button)

        main_layout.addWidget(dataset_label)
        main_layout.addLayout(dataset_folder_layout)
        main_layout.addWidget(sr_label)
        main_layout.addWidget(self.sr_combo_box)
        main_layout.addWidget(model_name_label)
        main_layout.addWidget(self.model_name_line_edit)
        main_layout.addWidget(f0method_label)
        main_layout.addWidget(self.f0method_combo_box)
        main_layout.addWidget(preprocess_button)
        main_layout.addWidget(extract_button)
        main_layout.addWidget(train_index_button)
        main_layout.addWidget(self.log_label)

        self.setWindowTitle("Обработка данных")

    def select_dataset_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с набором данных")
        if folder:
            self.dataset_folder_line_edit.setText(folder)
    def start_preprocess(self):
        dataset_folder = self.dataset_folder_line_edit.text()
        # Получаем выбранное значение и преобразуем его в числовой формат
        sample_rate = self.sr_combo_box.currentText()
        if sample_rate == "32k":
            sr = "32000"
        elif sample_rate == "40k":
            sr = "40000"
        elif sample_rate == "48k":
            sr = "48000"
        model_name = self.model_name_line_edit.text()

        if dataset_folder and model_name:
            self.preprocess_thread = PreprocessThread(dataset_folder, sr, model_name)
            self.preprocess_thread.update_log.connect(self.update_log)
            self.preprocess_thread.start()
        else:
            self.update_log("Пожалуйста, заполните все поля.")
            
    def start_preprocess(self):
        dataset_folder = self.dataset_folder_line_edit.text()
        sr = int(self.sr_combo_box.currentText())
        model_name = self.model_name_line_edit.text()

        if dataset_folder and model_name:
            self.preprocess_thread = PreprocessThread(dataset_folder, sr, model_name)
            self.preprocess_thread.update_log.connect(self.update_log)
            self.preprocess_thread.start()
        else:
            self.update_log("Пожалуйста, заполните все поля.")

    def start_extract(self):
        model_name = self.model_name_line_edit.text()
        f0method = self.f0method_combo_box.currentText()

        if model_name:
            self.extract_thread = ExtractThread(f0method, model_name)
            self.extract_thread.update_log.connect(self.update_log)
            self.extract_thread.start()
        else:
            self.update_log("Пожалуйста, введите имя модели.")

    def start_train_index(self):
        model_name = self.model_name_line_edit.text()

        if model_name:
            self.train_index_thread = TrainIndexThread(model_name)
            self.train_index_thread.update_log.connect(self.update_log)
            self.train_index_thread.start()
        else:
            self.update_log("Пожалуйста, введите имя модели.")

    def update_log(self, message):
        self.log_label.setText(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())