import torch
import torchaudio
from softvc.model import VITSNet
from softvc.utils import Preprocessor

# Загрузка предварительно обученной модели
model_path = r"C:\Users\mihei\Desktop\NoizeMC_e750_s12000.pth.pth"
vits = VITSNet.from_pretrained(model_path)

# Предварительная обработка аудио
preprocessor = Preprocessor()
audio_path = r"C:\Users\mihei\Desktop\Arlekino\vocals.wav"
audio, sr = torchaudio.load(audio_path)
mel = preprocessor(audio)

# Преобразование голоса
with torch.no_grad():
    converted_mel = vits.convert(mel)

# Сохранение преобразованного аудио
converted_audio = preprocessor.inv_mel2audio(converted_mel)
output_path = r"C:\Users\mihei\Desktop\Arlekino\converted_audio.wav"
torchaudio.save(output_path, converted_audio.squeeze(), sample_rate=sr)
