import glob
import os
from pathlib import Path
import io
import sys
import torch
import numpy as np
import soundfile

print(Path.cwd())
sys.path.append(os.path.dirname(__file__))

from inference import infer_tool, slicer
from inference.infer_tool import Svc

def convert(input_path, save_path, speaker, transpose : int = 0, cluster_ratio : float = 0.0,
             isAutoPitchChecked : bool = False, noise_scale : float = 0.5, slice_db : int = -40):
    
    torch.cuda.empty_cache()

    if not input_path:
            torch.cuda.empty_cache()
            return False

    svc_model = Svc(speaker["model_path"], speaker["cfg_path"], cluster_model_path=speaker["cluster_path"])

    buffer = np.array([])    
    audio_part_template = str(Path(input_path) / "*.wav")
    input_filepaths = glob.glob(audio_part_template)
    print(input_filepaths)
    for name in input_filepaths:
        print("Converting " + os.path.split(name)[-1])
        infer_tool.format_wav(name)
        wav_path = str(Path(name).with_suffix('.wav'))
        wav_name = Path(name).stem
        chunks = slicer.cut(wav_path, db_thresh=slice_db)
        audio_data, audio_sr = slicer.chunks2audio(wav_path, chunks)

        audio_data = sorted(audio_data)
        
        audio = []
        for (slice_tag, data) in audio_data:
            print(f'#=====segment start, {round(len(data)/audio_sr, 3)}s======')
            length = int(np.ceil(len(data) / audio_sr * svc_model.target_sample))

            if slice_tag:
                print('jump empty segment')
                _audio = np.zeros(length)
            else:
                pad_len = int(audio_sr * 0.5)
                data = np.concatenate([np.zeros([pad_len]), data, np.zeros([pad_len])])
                raw_path = io.BytesIO()  # Создаем объект BytesIO
                soundfile.write(raw_path, data, audio_sr, format="wav")
                raw_path.seek(0)
                _cluster_ratio =    0.0
                if speaker["cluster_path"] != "":
                    _cluster_ratio = cluster_ratio

                out_audio, out_sr = svc_model.infer(
                    speaker["name"], transpose, raw_path,
                    cluster_infer_ratio=_cluster_ratio,
                    auto_predict_f0=isAutoPitchChecked,
                    noice_scale=noise_scale)
                _audio = out_audio.cpu().numpy()
                pad_len = int(svc_model.target_sample * 0.5)
                _audio = _audio[pad_len:-pad_len]
            audio.extend(list(infer_tool.pad_array(_audio, length)))
        buffer = np.concatenate((buffer, audio))

    res_path = os.path.join(save_path, f'{wav_name}_noway_{transpose}_key_{speaker["name"]}.wav')
    soundfile.write(res_path, buffer, svc_model.target_sample, format="wav")
    print(f"Converted audio saved to {res_path}")  # Добавляем вывод сообщения о сохранении файла