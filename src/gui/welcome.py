from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Текст сверху: "Добро пожаловать в программу для работы с записями"
        self.welcome_label = QLabel("Добро пожаловать в программу для работы с записями.")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 18px;")  # Увеличенный шрифт
        layout.addWidget(self.welcome_label)

        layout.addStretch()

        # Текст снизу: "Выберите, что вы желаете сделать"
        self.choose_action_label = QLabel("Выберите, что Вы желаете сделать:")
        self.choose_action_label.setAlignment(Qt.AlignCenter)
        self.choose_action_label.setStyleSheet("font-size: 16px;")  # Немного меньший шрифт
        layout.addWidget(self.choose_action_label)

        # Кнопка "Создать модель"
        self.create_model_button = QPushButton("Создать модель")
        self.create_model_button.setFixedSize(300, 60)  # Увеличиваем размер кнопки
        self.create_model_button.setStyleSheet("font-size: 16px;")  # Увеличиваем размер шрифта кнопки
        layout.addWidget(self.create_model_button, 0, Qt.AlignCenter)

        # Кнопка "Обработать аудио запись"
        self.process_audio_button = QPushButton("Обработать аудио запись")
        self.process_audio_button.setFixedSize(300, 60)  # Увеличиваем размер кнопки
        self.process_audio_button.setStyleSheet("font-size: 16px;")  # Увеличиваем размер шрифта кнопки
        layout.addWidget(self.process_audio_button, 0, Qt.AlignCenter)

        # Кнопка "Выход"
        self.exit_button = QPushButton("Выход")
        self.exit_button.setFixedSize(300, 60)  # Увеличиваем размер кнопки
        self.exit_button.setStyleSheet("font-size: 16px;")  # Увеличиваем размер шрифта кнопки
        layout.addWidget(self.exit_button, 0, Qt.AlignCenter)

        # Добавляем пространство снизу
        layout.addStretch()

        # Делаем кнопку "Создать модель" кликабельной (на данный момент без действия)
        self.create_model_button.clicked.connect(self.on_create_model_clicked)

        self.setLayout(layout)

    def on_create_model_clicked(self):
        # Пока просто выводим сообщение в консоль
        print("Кнопка 'Создать модель' нажата")