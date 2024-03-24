import tensorflow as tf
from tensorflow.keras import layers, models
import librosa
import numpy as np

# Функция для загрузки аудиофайлов и извлечения признаков
def load_and_extract_features(audio_files):
    features = []
    labels = []
    for file, label in audio_files:  # Добавлено получение метки из входных данных
        # Загрузка аудиофайла
        audio, sr = librosa.load(file, sr=None)
        # Извлечение признаков, например, используя mel-спектрограмму
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr)
        # Преобразование в логарифмическую шкалу
        log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
        # Добавление в список признаков
        features.append(log_mel_spec)
        # Добавление метки (label) в соответствии с файлом
        labels.append(label)
    return np.array(features), np.array(labels)

# Загрузка данных для обучения
audio_files = [("C:\\Users\\mihei\\Desktop\\Arlekino\\vocals.wav", 1)]  # Добавлено определение метки для файла
training_features, training_labels = load_and_extract_features(audio_files)

# Расширение размерности массива признаков для работы с Conv2D
training_features = np.expand_dims(training_features, axis=-1)

# Создание модели нейронной сети
model = models.Sequential([
    layers.Input(shape=training_features.shape[1:]),  # Изменено определение входной формы
    layers.Conv2D(32, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(1, activation='sigmoid')  # Изменено количество нейронов в выходном слое и функция активации
])

# Компиляция модели
model.compile(optimizer='adam',
              loss='binary_crossentropy',  # Используем бинарную кросс-энтропию для бинарной классификации
              metrics=['accuracy'])

# Обучение модели
history = model.fit(training_features, training_labels, epochs=10)

# Вывод информации о процессе обучения
print("Обучение завершено. История обучения:")
print(history.history)
