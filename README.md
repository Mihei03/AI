# AI Cover 

[![Typing SVG](https://readme-typing-svg.herokuapp.com?color=%2336BCF7&lines=Insane+AI+Covers)](https://git.io/typing-svg)

Сервис для создания нейро-каверов на песни, объединяющий и упрощающий использование нескольких инструментов.
## Оглавление
[Требования](#Требование)  
[Зависимости](#Зависимости)  
[Использование](#Использование)  
[В планах](#В_планах)  
[Требование](#Требования)  
## Зависимости
- [Скачать python 3.8](https://www.python.org/downloads/release/python-380/)
- После обычной установки, запустите установку ещё раз и сделайте следующее:
![python.png](Readme/python.jpg)
![python1.png](Readme/python1.jpg)
![python2.png](Readmepython2.jpg)
- [Скачать ffmpeg](https://ffmpeg.org/download.html)
- Установка:
- Перейдите в C:\Program Files и расспакуйте архив.
- Перейдите в C:\Program Files\ffmpeg-6.1.1-full_build\bin, убедитесь, что там 3 файла.
- После чего откройте "Изменение системных переменных среды", нажмите на "Переменные среды...", в Переменные среды пользователя и просто Системные переменные найдите Path и добавьте путь из прошлого пункта (C:\Program Files\ffmpeg-6.1.1-full_build\bin). После чего нажмите "Ок" и закройте. (Лучше будет, если перезапустите пк)
- После этого этапа, откройте командную строку (Win+R, cmd)
- Пропишите в консоли:
- pip install spleeter
- pip install ffmpeg-python
- После закройте окно cmd и откройте его снова.
- Для проверки работоспособности перейдите в консоли в папку, где есть музыка (cd название папки, пока не дойдёте до папки с музыкой для обработки)
- Впишите команду: spleeter separate -p spleeter:2stems -o output audio_example.mp3
- Если всё работает - супер! Рад за вас, если нет, то ищите способы решения проблем сами.
## Инструменты
- python 3.8
- ffmpeg
- spleeter - библиотека для разделения аудиофайла на вокал и минус
- SoftVC VITS Singing Voice Conversion - нейросеть для изменения вокала
- pydub - соединение изменённого вокала и минуса
- PyQt - создание полноценного GUI 
## Использование
- Для того, чтобы использовать альфа-версию продукта перейдите в папку dist в котором находится AI.exe.
![Нужная папка](Readme/dist.png)
![AI.exe](Readme/AI.png)

- После запуска вы увидите маленькое окно в котором на данный момент есть "Выбор файла" (1) который будет обрабатываться, "Выбор папки" (2) куда будет сохранятся обработка, так же есть варианты обработки (3), которые можно менять (2, 4 и 5), где 
- 2 - Vocals / accompaniment separation
- 4 - Vocals / drums / bass / other separation
- 5 - Vocals / drums / bass / piano / other separation<br> 
![Пример программы](Readme/alpha1.png)
- После нажатия на кнопку "Выбрать файл" (1) появится проводник в котором нужно выбрать желаемый файл для обработки (Для примера был выбран файл - Цой.mp3).
![Пример программы](Readme/Choice.png)
- После выбора вы сумеете указать папку, где будет создана папка с обработанной музыкой (По умолчанию это "Рабочий стол").
- Следующий шаг - выбрать вариант обработки (По умолчанию стоит 2-о1 вариант).
- При нажатии на кнопку "Обработать аудио", программа начнёт разделять аудиофайл на компоненты, которые вы выбрали в прошлом пункте. 
## !Если программа зависла, ничего не трогайте, идёт обработка, которая займёт от 1 до 4 минут!
- В конце работы вы получите папку, в которой будет разделённый аудиофайл.
## Если папки dist нет, то соберите программу сами:
- Установите pyinstaller, если у вас его еще нет, с помощью pip: pip install pyinstaller
- Перейдите в каталог, содержащий ваш Python-скрипт, используя командную строку.
- Затем запустите pyinstaller, указав путь к скрипту: pyinstaller AI.py 
## В планах
- [ ] Установка всех зависимостей
    - [x] spleeter
    - [ ] SoftVC VITS Singing Voice Conversion
    - [ ] pydub
- [x] Минимальный консольный UI  
- [ ] Реализация изменения голоса 
- [ ] Слияние звуковых дорожек
- [ ] полноценный GUI
## ЧаВо
## Источники

[Оглавление](#Оглавление)
