import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox
from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QSpacerItem, QSizePolicy
from pathlib import Path
import shutil

project_root = Path(__file__).parent
sys.path.append(str(project_root))

import copy
import glob
import os
import json

from src.audio.audio_separation import separate


class SeparationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.song_path = None
        self.save_path = None

    def initUI(self):
        layout = QVBoxLayout()

        song_layout = QHBoxLayout()
        self.song_label = QLabel("Выбранная песня: ")
        self.song_label.setStyleSheet("font-size: 16px;")
        song_layout.addWidget(self.song_label)
        self.select_song_button = QPushButton("Выбор песни")
        self.select_song_button.setStyleSheet("font-size: 16px;")
        self.select_song_button.clicked.connect(self.select_song)
        song_layout.addWidget(self.select_song_button)
        layout.addLayout(song_layout)
        layout.addStretch(10)

        self.split_label = QLabel("Выберите вариант обработки:")
        self.split_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.split_label)

        self.split_options = QComboBox()
        self.split_options.addItems([
            "2 - Vocals / accompaniment separation",
            "4 - Vocals / drums / bass / other separation",
            "5 - Vocals / drums / bass / piano / other separation"
        ])
        self.split_options.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.split_options)

        # Добавляем небольшой отступ после комбобокса
        layout.addStretch(5)

        # Центрирование и увеличение кнопки "Сохранить отдельно"
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_button = QPushButton("Сохранить отдельно")
        self.save_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                min-width: 200px;
                min-height: 40px;
            }
        """)
        self.save_button.clicked.connect(self.save_file)
        save_layout.addWidget(self.save_button)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        self.save_path_label = QLabel()
        layout.addWidget(self.save_path_label)

        # Добавляем отступ перед кнопками навигации
        layout.addSpacing(20)

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

    def select_song(self):
        default_dir = os.path.join(os.getcwd(), "src", "SOVITS", "песни")
        # Создаем директорию, если она не существует
        os.makedirs(default_dir, exist_ok=True)
        
        file_dialog = QFileDialog(self)
        file_dialog.setDirectory(default_dir)  # Устанавливаем начальную директорию
        self.song_path, _ = file_dialog.getOpenFileName(
            self,
            "Выбрать песню",
            default_dir,
            "Audio Files (*.mp3 *.wav)"
        )
        if self.song_path:
            self.song_label.setText(f"Выбранная песня: {self.song_path}")

    def save_file(self):
        if not self.song_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите песню для обработки.")
            return

        file_dialog = QFileDialog()
        self.save_path = file_dialog.getExistingDirectory(self, "Выбрать путь для сохранения")
        if self.save_path:
            self.save_path_label.setText(f"Сохраняется в: {self.save_path}")
            split_option = int(self.split_options.currentText().split(' - ')[0])
            input_file = Path(self.song_path)
            output_dir = Path(self.save_path)

            try:
                # Создаем временную директорию
                temp_dir = Path.cwd() / "temp"
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                temp_dir.mkdir(exist_ok=True)

                # Выполняем разделение
                separate(split_option, input_file, temp_dir)

                # Перемещаем результаты в выбранную директорию
                for file in temp_dir.glob('*'):
                    shutil.move(str(file), str(output_dir))

                # Удаляем временную директорию
                shutil.rmtree(temp_dir)

                QMessageBox.information(self, "Успех", f"Файлы успешно сохранены в {self.save_path}")
                self.next_button.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении: {str(e)}")
