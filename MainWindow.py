import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow,QCheckBox, QMessageBox, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QStackedWidget, QHBoxLayout
from PyQt5.QtCore import QStandardPaths, Qt, QSize

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Processor")
        self.setGeometry(100, 100, 400, 300)

        self.window_sizes = {
            0: QSize(400, 300),  # Размер окна для первой вьюшки
            1: QSize(400, 350),  # Размер окна для второй вьюшки
            2: QSize(400, 300),  # Размер окна для третьей вьюшки
            3: QSize(600, 550),  # Размер окна для четвертой вьюшки
            4: QSize(200, 400)   # Размер окна для пятой вьюшки
    }    
        # Создаем стековый виджет для переключения между вьюшками
        self.stack = QStackedWidget()
        self.stack.currentChanged.connect(self.set_window_size)

        # Первая вьюшка - описание программы
        starting_widget = QWidget()
        starting_layout = QVBoxLayout()
        description_label = QLabel("Это программа для обработки аудиофайлов.\nВыберите файл, вариант обработки и сохраните результат.", self)
        description_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        start_button = QPushButton("Начать")
        start_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        starting_layout.addWidget(description_label)
        starting_layout.addWidget(start_button)

        starting_widget.setLayout(starting_layout)
        self.stack.addWidget(starting_widget)

        # Вторая вьюшка - выбор файла и параметров обработки
        separating_widget = QWidget()
        separating_layout = QVBoxLayout()

        separation = QLabel("Разделение\n", self)
        separation.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.audio_file_label = QLabel("Выберите файл для обработки:")
        self.audio_file_line = QLineEdit()
        self.audio_file_line.setReadOnly(True)
        self.select_button = QPushButton("Выбрать файл")
        self.select_button.clicked.connect(self.handle_input)

        self.treatment_label = QLabel("Выбери вариант обработки (2, 4, 5) \n- 2 - Vocals / accompaniment separation \n- 4 - Vocals / drums / bass / other separation \n- 5 - Vocals / drums / bass / piano / other separation:")
        self.treatment_combo = QComboBox()
        self.treatment_combo.addItems(["2", "4", "5"])

        self.save_button = QPushButton("Сохранить")

        self.output_treatment_button = QPushButton("Сохранить как...")
        self.output_treatment_button.clicked.connect(self.handle_output)

        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.next_button = QPushButton("Далее")
        self.next_button.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        separating_layout.addWidget(separation)
        separating_layout.addWidget(self.audio_file_label)
        separating_layout.addWidget(self.audio_file_line)
        separating_layout.addWidget(self.select_button)
        separating_layout.addWidget(self.treatment_label)
        separating_layout.addWidget(self.treatment_combo)
        separating_layout.addWidget(self.save_button)
        separating_layout.addWidget(self.output_treatment_button)
        separating_layout.addLayout(self.create_button_layout())
        separating_widget.setLayout(separating_layout)
        self.stack.addWidget(separating_widget)

        # 3-я вьюшка - выбор модели
        model_widget = QWidget()
        model_layout = QVBoxLayout()

        RVC = QLabel("Выбор модели\n", self)
        RVC.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.next_button = QPushButton("Далее")
        self.next_button.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        model_layout.addWidget(RVC)
        model_layout.addLayout(self.create_button_layout())
        model_widget.setLayout(model_layout)
        self.stack.addWidget(model_widget)

        # 4-я вьюшка - обработка
        svc_widget = QWidget()
        svc_layout = QVBoxLayout()

        SVC = QLabel("Обработка\n", self)
        SVC.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.input_path_btn = QPushButton("Выбрать путь к входной песне")
        #self.input_path_btn.clicked.connect(self.select_input_path)
        self.input_path_label = QLabel("Путь к входной песне:")
        self.input_path_tx = QLineEdit()
        self.input_path_tx.setText(os.path.join(os.path.expanduser("~"), "Desktop"))
        self.input_path_tx.setReadOnly(True)
        
        self.model_path_btn = QPushButton("Выбрать путь к моделям")
        #self.model_path_btn.clicked.connect(self.select_model_path)
        self.model_path_label = QLabel("Путь к моделям:")
        self.model_path_tx = QLineEdit()
        #self.model_path_tx.setText(self.models_dir)
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
        #self.save_path_btn.clicked.connect(self.select_save_path)
        self.save_path_label = QLabel("Путь сохранения:")
        self.save_path_tx = QLineEdit()
        self.save_path_tx.setText(os.path.join(os.path.expanduser("~"), "Desktop"))
        self.save_path_btn.setEnabled(False)  # Изначально кнопка выбора пути сохранения заблокирована
        self.save_path_tx.setReadOnly(True)
        
        self.convert_btn = QPushButton("Конвертировать")
        #self.convert_btn.clicked.connect(self.convert)
        self.convert_btn.setEnabled(False)  # Изначально кнопка конвертировать заблокирована
        
        self.clean_btn = QPushButton("Удалить все аудиофайлы")
        #self.clean_btn.clicked.connect(self.clean)
        self.clean_btn.setEnabled(False)  # Изначально кнопка удаления аудиофайлов заблокирована
        
        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.next_button = QPushButton("Далее")
        self.next_button.clicked.connect(lambda: self.stack.setCurrentIndex(4))

        svc_layout.addWidget(SVC)
        svc_layout.addWidget(self.input_path_label)
        svc_layout.addWidget(self.input_path_tx)
        svc_layout.addWidget(self.input_path_btn)
        svc_layout.addWidget(self.model_path_label)
        svc_layout.addWidget(self.model_path_tx)
        svc_layout.addWidget(self.model_path_btn)
        svc_layout.addWidget(self.speaker_label)
        svc_layout.addWidget(self.speaker_box)
        svc_layout.addWidget(self.trans_label)
        svc_layout.addWidget(self.trans_tx)
        svc_layout.addWidget(self.cluster_ratio_label)
        svc_layout.addWidget(self.cluster_ratio_tx)
        svc_layout.addWidget(self.noise_scale_label)
        svc_layout.addWidget(self.noise_scale_tx)
        svc_layout.addWidget(self.auto_pitch_ck)
        svc_layout.addWidget(self.save_path_label)
        svc_layout.addWidget(self.save_path_tx)
        svc_layout.addWidget(self.save_path_btn)
        svc_layout.addWidget(self.convert_btn)
        svc_layout.addWidget(self.clean_btn)
        svc_layout.addLayout(self.create_button_layout())
        svc_widget.setLayout(svc_layout)

        self.stack.addWidget(starting_widget)
        self.stack.addWidget(separating_widget)
        self.stack.addWidget(model_widget)
        self.stack.addWidget(svc_widget)

        central_widget = QWidget()
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(self.stack)
        self.setCentralWidget(central_widget)


    def create_button_layout(self):
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.next_button)
        return button_layout

    def handle_input(self):
        audio_file, _ = QFileDialog.getOpenFileName(self, "Выберите файл для обработки", "", "All Files (*);;MP3 Files (*.mp3)")
        if audio_file:
            if not audio_file.endswith('.mp3'):
                QMessageBox.warning(self, "Предупреждение", "Выберите файл формата MP3.")
                return
            self.audio_file_path = audio_file
            self.audio_file_line.setText(self.audio_file_path)

    def handle_output(self):
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        if desktop_path:
            output_folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения обработанных файлов", desktop_path)
            if output_folder:
                self.output_folder_path = output_folder
                self.output_folder_line.setText(self.output_folder_path)
            else:
                QMessageBox.critical(self, "Ошибка", "Папка для сохранения обработанных файлов не выбрана.")
        else:
            QMessageBox.critical(self, "Ошибка", "Рабочий стол не найден.")

    def set_window_size(self, index):
        if index in self.window_sizes:
            self.setFixedSize(self.window_sizes[index])
        else:
            self.setMinimumSize(QSize(200, 100))


def show():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())