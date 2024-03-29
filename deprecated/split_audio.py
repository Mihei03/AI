import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QSpinBox, QFileDialog, QMessageBox, QLineEdit, QComboBox  
from PyQt5.QtCore import QDir, QStandardPaths

class AudioProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.audio_file_path = ""
        self.treatment = "2"
        self.output_folder_path = ""
        self.init_ui()

    def handle_input(self):
        audio_file, _ = QFileDialog.getOpenFileName(self, "Выберите файл для обработки", "", "All Files (*);;MP3 Files (*.mp3)")
        if audio_file:
            if not audio_file.endswith('.mp3'):
                QMessageBox.warning(self, "Предупреждение", "Выберите файл формата MP3.")
                return
            self.audio_file_path = audio_file
            self.audio_file_line.setText(self.audio_file_path)
            self.audio_treatment_line.setEnabled(True)
            self.output_treatment_button.setEnabled(True)

    def handle_output(self):
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        if desktop_path:
            output_folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения обработанных файлов", desktop_path)
            if output_folder:
                self.output_folder_path = output_folder
                self.output_folder_line.setText(self.output_folder_path)
                self.audio_treatment_line.setEnabled(True)
                self.output_treatment_button.setEnabled(True)
                self.process_button.setEnabled(True)
                self.treatment_combo.setEnabled(True)
            else:
                QMessageBox.critical(self, "Ошибка", "Папка для сохранения обработанных файлов не выбрана.")
        else:
            QMessageBox.critical(self, "Ошибка", "Рабочий стол не найден.")


    def process_audio(self):
        if not self.audio_file_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите файл для обработки.")
            return

        if not self.output_folder_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите папку для сохранения файла.")
            return

        treatment = self.treatment_combo.currentText()  # Использование текущего выбранного значения из комбобокса
        command = f'spleeter separate -p spleeter:{treatment}stems -o "{self.output_folder_path}" "{self.audio_file_path}"'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        output, error = process.communicate()

        if process.returncode == 0:
            QMessageBox.information(self, "Успех", "Аудио успешно обработано!")
        else:
            QMessageBox.critical(self, "Ошибка", "Произошла ошибка при обработке аудио.")

    def init_ui(self):
        self.setWindowTitle("Audio Processor")
        self.setGeometry(100, 100, 400, 300)

        self.audio_file_label = QLabel("Выберите файл для обработки:")
        self.audio_file_line = QLineEdit()
        self.select_button = QPushButton("Выбрать файл")
        self.select_button.clicked.connect(self.handle_input)

        self.audio_treatment_label = QLabel("Выберите место для сохранения обработанных файлов:")
        self.output_folder_line = QLineEdit()
        self.output_treatment_button = QPushButton("Выбрать папку для сохранения обработанного аудио файла")
        self.output_treatment_button.clicked.connect(self.handle_output)
        self.output_treatment_button.setEnabled(False)

        self.treatment_label = QLabel("Выбери вариант обработки (2, 4, 5):")
        self.treatment_line = QSpinBox()
        self.treatment_line.setValue(int(self.treatment))
        self.treatment_line.setEnabled(False)

        self.treatment_label = QLabel("Выбери вариант обработки (2, 4, 5) \n- 2 - Vocals / accompaniment separation \n- 4 - Vocals / drums / bass / other separation \n- 5 - Vocals / drums / bass / piano / other separation:")
        self.treatment_combo = QComboBox()  # Замена QSpinBox на QComboBox
        self.treatment_combo.addItems(["2", "4", "5"])  # Добавление вариантов обработки
        self.treatment_combo.setCurrentText(self.treatment)  # Установка значения по умолчанию
        self.treatment_combo.setEnabled(False)

        self.audio_treatment_label = QLabel("Выберите место для сохранения обработанных файлов:")
        self.audio_treatment_line = QLineEdit() 
        self.audio_treatment_line.setEnabled(False)  

        self.process_button = QPushButton("Обработать аудио")
        self.process_button.clicked.connect(self.process_audio)
        self.process_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.audio_file_label)
        layout.addWidget(self.audio_file_line)
        layout.addWidget(self.select_button)

        layout.addWidget(self.audio_treatment_label)
        layout.addWidget(self.output_folder_line)
        layout.addWidget(self.output_treatment_button)

        layout.addWidget(self.treatment_label)
        layout.addWidget(self.treatment_combo)
        
        layout.addWidget(self.process_button)

        self.setLayout(layout)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AudioProcessorApp()
    sys.exit(app.exec_())
