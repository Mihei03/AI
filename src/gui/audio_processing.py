from PyQt5.QtWidgets import QWidget, QSpinBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QListWidget, QListWidgetItem, QFileDialog, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
from pydub import AudioSegment
import tempfile
import os
import pygame

class AudioPlayThread(QThread):
    finished = pyqtSignal()

    def __init__(self, audio_file):
        super().__init__()
        self.audio_file = audio_file
        self.is_playing = True

    def run(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and self.is_playing:
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.finished.emit()

    def stop(self):
        self.is_playing = False

class AudioProcessingWindow(QWidget):
    def __init__(self, temp_dir):
        super().__init__()
        self.temp_dir = Path(temp_dir)
        self.initUI()
        self.load_audio_files()
        self.current_audio = None
        self.play_thread = None
        self.is_playing = False
        self.temp_audio_file = None

    def initUI(self):
        layout = QVBoxLayout()

        # Список аудиофайлов
        self.file_list = QListWidget()
        layout.addWidget(QLabel("Аудиофайлы:"))
        self.file_list.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.file_list)
        self.file_list.itemClicked.connect(self.reset_volume_spinbox)

        # Элементы управления воспроизведением
        player_layout = QHBoxLayout()
        self.play_button = QPushButton("Воспроизвести")
        self.play_button.setStyleSheet("font-size: 14px;")
        self.play_button.clicked.connect(self.play_audio)
        player_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Остановить")
        self.stop_button.setStyleSheet("font-size: 14px;")
        self.stop_button.clicked.connect(self.stop_audio)
        player_layout.addWidget(self.stop_button)

        layout.addLayout(player_layout)

        # Регулятор громкости
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Громкость (дБ):"))
        self.volume_spinbox = QSpinBox()
        self.volume_spinbox.setRange(-60, 20)  # Расширенный диапазон для уменьшения громкости
        self.volume_spinbox.setValue(0)
        self.volume_spinbox.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_spinbox)
        layout.addLayout(volume_layout)

        # Кнопка для объединения выбранных треков
        self.merge_button = QPushButton("Объединить выбранные треки")
        self.merge_button.setStyleSheet("font-size: 14px;")
        self.merge_button.clicked.connect(self.merge_selected_tracks)
        layout.addWidget(self.merge_button)

        # Навигационные кнопки
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Назад")
        self.back_button.setStyleSheet("font-size: 14px;")
        self.back_button.clicked.connect(self.back_to_model_selection)
        nav_layout.addWidget(self.back_button)
        
        self.home_button = QPushButton("Вернуться в начало программы")
        self.home_button.setStyleSheet("font-size: 14px;")
        self.home_button.clicked.connect(self.back_to_main_menu)
        nav_layout.addWidget(self.home_button)
        
        layout.addLayout(nav_layout)

        self.setLayout(layout)

    def reset_volume_spinbox(self):
        self.volume_spinbox.setValue(0)  # Сбрасываем значение спинбокса на 0

    def load_audio_files(self):
        self.file_list.clear()  # Очищаем список перед загрузкой
        for file in self.temp_dir.glob('*.wav'):
            if file.exists():  # Проверяем, существует ли файл
                item = QListWidgetItem(file.name)
                item.setCheckState(Qt.Unchecked)
                self.file_list.addItem(item)

    def play_audio(self):
        if self.is_playing:
            return  # Если уже проигрывается, ничего не делаем

        current_item = self.file_list.currentItem()
        if current_item:
            self.reset_volume_spinbox()  # Сбрасываем значение спинбокса перед воспроизведением
            file_path = self.temp_dir / current_item.text()
            if not file_path.exists():
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {file_path}")
                return

            try:
                # Загружаем аудио и применяем изменения
                audio = AudioSegment.from_wav(str(file_path))
                
                # Применяем изменение громкости
                volume_change = self.volume_spinbox.value()
                if volume_change != 0:
                    audio = audio + volume_change  # pydub использует dB

                # Сохраняем изменения во временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    audio.export(temp_file.name, format="wav")
                    self.temp_audio_file = temp_file.name

                # Блокируем все элементы управления, кроме кнопки остановки
                self.file_list.setEnabled(False)
                self.volume_spinbox.setEnabled(False)
                self.play_button.setEnabled(False)
                self.merge_button.setEnabled(False)
                self.back_button.setEnabled(False)
                self.home_button.setEnabled(False)

                # Воспроизводим с помощью pygame в отдельном потоке
                self.play_thread = AudioPlayThread(self.temp_audio_file)
                self.play_thread.finished.connect(self.on_playback_finished)
                self.play_thread.start()
                self.is_playing = True

            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка при воспроизведении аудио: {str(e)}")
                self.is_playing = False
                self.enable_all_controls()

    def stop_audio(self):
        if self.is_playing and self.play_thread:
            self.play_thread.stop()
            self.play_thread.wait()
            self.on_playback_finished()

    def on_playback_finished(self):
        self.is_playing = False
        self.enable_all_controls()
        if self.temp_audio_file:
            os.unlink(self.temp_audio_file)
            self.temp_audio_file = None

    def enable_all_controls(self):
        self.file_list.setEnabled(True)
        self.volume_spinbox.setEnabled(True)
        self.play_button.setEnabled(True)
        self.merge_button.setEnabled(True)
        self.back_button.setEnabled(True)
        self.home_button.setEnabled(True)

    def change_volume(self):
        if not self.is_playing:
            current_item = self.file_list.currentItem()
            if current_item:
                file_path = self.temp_dir / current_item.text()
                if file_path.exists():
                    audio = AudioSegment.from_wav(str(file_path))
                    volume_change = self.volume_spinbox.value()
                    audio = audio + volume_change
                    audio.export(str(file_path), format="wav")

    def set_main_app(self, main_app):
        self.main_app = main_app

    def back_to_model_selection(self):
        main_app = self.parent()
        main_app.show_model_selection_window()

    def back_to_main_menu(self):
        main_app = self.parent()
        main_app.show_welcome_window()

    def merge_selected_tracks(self):
        selected_tracks = []
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            if item.checkState() == Qt.Checked:
                file_path = self.temp_dir / item.text()
                if file_path.exists():
                    selected_tracks.append(str(file_path))

        if len(selected_tracks) < 2:
            QMessageBox.warning(self, "Ошибка", "Выберите как минимум два трека для объединения")
            return

        file_name, ok = QInputDialog.getText(self, 'Сохранение файла', 'Введите имя файла:')
        if ok and file_name:
            temp_output_path = self.temp_dir / f"{file_name}.wav"
            output_path = Path(self.temp_dir.parent.parent, "output") / f"{file_name}.wav"
            
            try:
                # Загружаем первый трек
                merged_audio = AudioSegment.from_wav(selected_tracks[0])
                
                # Добавляем остальные треки
                for track in selected_tracks[1:]:
                    audio = AudioSegment.from_wav(track)
                    merged_audio = merged_audio.overlay(audio)
                
                # Экспортируем объединенный трек
                merged_audio.export(str(temp_output_path), format="wav")
                merged_audio.export(str(output_path), format="wav")
                
                QMessageBox.information(self, "Успех", f"Треки объединены и сохранены в {temp_output_path} и {output_path}")
                
                self.load_audio_files()  # Обновляем список файлов
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось объединить треки: {str(e)}")
        else:
            QMessageBox.information(self, "Отмена", "Отменено сохранение файла")

    def closeEvent(self, event):
        self.stop_audio()
        super().closeEvent(event)
