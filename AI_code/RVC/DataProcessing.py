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
            print("Обрабатываем датасет...")
        cmd = f'python infer/modules/train/preprocess.py {self.dataset_folder} {self.sr} 2 ./logs/{self.model_name} False 3.0'
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
            print("Запуск обработки...")
        if self.f0method != "rmvpe_gpu":
            cmd = f'python C:/Users/mihei/Desktop/RVC/TrainVocModel/infer/modules/train/extract/extract_f0_print.py ./logs/{self.model_name} 2 {self.f0method}'
            os.system(cmd)
        else:
            cmd = f'python infer/modules/train/extract/extract_f0_rmvpe.py 1 0 0 ./logs/{self.model_name} True'
            os.system(cmd)
        cmd = f'python infer/modules/train/extract_feature_print.py cuda:0 1 0 ./logs/{self.model_name} v2 True'
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
    exp_dir = f"logs/{exp_dir1}"
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
    index_ivf = faiss.extract_index_ivf(index)  #
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
        index.add(big_npy[i: i + batch_size_add])
    faiss.write_index(
        index,
        f"{exp_dir}/added_IVF{n_ivf}_Flat_nprobe_{index_ivf.nprobe}_{exp_dir1}_{version19}.index"
    )
    infos.append(
        f"успешно построен индекс, added_IVF{n_ivf}_Flat_nprobe_{index_ivf.nprobe}_{exp_dir1}_{version19}.index"
    )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обработка данных")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        layout = QVBoxLayout()

        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("Введите имя модели")
        layout.addWidget(QLabel("Имя модели:"))
        layout.addWidget(self.model_name_input)

        self.dataset_folder_input = QLineEdit()
        self.dataset_folder_input.setPlaceholderText("Выберите папку с данными")
        browse_button = QPushButton("Обзор")
        browse_button.clicked.connect(self.browse_folder)
        dataset_folder_layout = QHBoxLayout()
        dataset_folder_layout.addWidget(self.dataset_folder_input)
        dataset_folder_layout.addWidget(browse_button)
        layout.addWidget(QLabel("Папка с данными:"))
        layout.addLayout(dataset_folder_layout)

        self.sr_input = QLineEdit()
        self.sr_input.setPlaceholderText("Введите частоту дискретизации")
        layout.addWidget(QLabel("Частота дискретизации:"))
        layout.addWidget(self.sr_input)

        self.f0method_combo = QComboBox()
        self.f0method_combo.addItems(["pm", "pmvmr", "rmvpe_gpu"])
        layout.addWidget(QLabel("Метод извлечения F0:"))
        layout.addWidget(self.f0method_combo)

        self.log_label = QLabel()
        layout.addWidget(self.log_label)

        preprocess_button = QPushButton("Предварительная обработка")
        preprocess_button.clicked.connect(self.preprocess_data)
        layout.addWidget(preprocess_button)

        extract_button = QPushButton("Извлечь признаки")
        extract_button.clicked.connect(self.extract_features)
        layout.addWidget(extract_button)

        train_button = QPushButton("Обучить индекс")
        train_button.clicked.connect(self.train_index)
        layout.addWidget(train_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с данными")
        self.dataset_folder_input.setText(folder_path)

    def preprocess_data(self):
        model_name = self.model_name_input.text()
        dataset_folder = self.dataset_folder_input.text()
        sr = self.sr_input.text()

        if not model_name or not dataset_folder or not sr:
            self.log_label.setText("Пожалуйста, введите все необходимые данные")
            return

        self.preprocess_thread = PreprocessThread(dataset_folder, sr, model_name)
        self.preprocess_thread.update_log.connect(self.log_label.setText)
        self.preprocess_thread.start()

    def extract_features(self):
        model_name = self.model_name_input.text()
        f0method = self.f0method_combo.currentText()

        if not model_name:
            self.log_label.setText("Пожалуйста, введите имя модели")
            return

        self.extract_thread = ExtractThread(f0method, model_name)
        self.extract_thread.update_log.connect(self.log_label.setText)
        self.extract_thread.start()

    def train_index(self):
        model_name = self.model_name_input.text()

        if not model_name:
            self.log_label.setText("Пожалуйста, введите имя модели")
            return

        self.train_index_thread = TrainIndexThread(model_name)
        self.train_index_thread.update_log.connect(self.log_label.setText)
        self.train_index_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())