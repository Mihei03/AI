from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.info_label = QLabel("Добро пожаловать в программу разделения аудио!")
        layout.addWidget(self.info_label)

        button_layout = QHBoxLayout()
        self.exit_button = QPushButton("Выход")
        button_layout.addWidget(self.exit_button)
        button_layout.addStretch()
        self.start_button = QPushButton("Начать")
        button_layout.addWidget(self.start_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)