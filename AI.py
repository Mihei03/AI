from spleeter.separator import Separator

# Создаем экземпляр Separator с конфигурацией spleeter:2stems для разделения на 2 стемы
separator = Separator('spleeter:2stems')

# Укажите путь к входному аудиофайлу
audio_file = 'Arlekino.mp3'

# Вызываем метод separate для разделения аудиофайла
separator.separate_to_file(audio_file, 'output/')
