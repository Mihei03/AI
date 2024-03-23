import subprocess
import os
import inspect

base_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
spleeter_executable = 'spleeter'
audio_file_path = ""

def handle_input():
    global audio_file_path
    while True:
        audio_file = input("Напиши название файла для обработки (без расширения): ")
        audio_file_path = os.path.join(base_folder, f"песни\\{audio_file}.mp3")
        if not os.path.exists(audio_file_path):
            print(f"Файл с именем '{audio_file}.mp3' не найден в папке 'песни'. Проверьте правильность имени файла.\n")
        else:
            break

    return audio_file, audio_file_path


print('Привет! Пожалуйста, ответь, что и как ты хочешь обработать:')
audio_file = handle_input()

print('Доступны 3 варианта обработки: \nVocals/accompaniment - 2 \nVocals/drums/bass/other - 4 \nVocals/drums/bass/piano/other - 5 \n')

while True:
    treatment = input("Выбери вариант обработки: ")
    if treatment in ['2', '4', '5']:
        break
    print('Некорректный вариант обработки. Пожалуйста, выбери 2, 4 или 5.\n')

current_directory = os.path.dirname(__file__)
command = f'{spleeter_executable} separate -p spleeter:{treatment}stems -o {current_directory}обработка/ "{audio_file_path}"'

# Запуск процесса разделения через командную строку
subprocess.run(command, shell=True)

print('Аудио успешно разделено!')
