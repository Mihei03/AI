import io
import os
from pathlib import Path
from inference import infer_tool, slicer
from inference.infer_tool import Svc
import numpy as np
import soundfile


def convert(input_path, trans_text, speakers, 
            speakerbox_text, cluster_ratio_text,isAutoPitchChecked,
            noise_scale_text,save_path, slice_db):
    
    if not input_path:
            return False
        
    trans = int(trans_text)
    speaker = next(x for x in speakers if x["name"] == speakerbox_text)

    svc_model = Svc(speaker["model_path"], speaker["cfg_path"], cluster_model_path=speaker["cluster_path"])

    input_filepaths = [input_path]
    for name in input_filepaths:
        print("Converting " + os.path.split(name)[-1])
        infer_tool.format_wav(name)
        wav_path = str(Path(name).with_suffix('.wav'))
        wav_name = Path(name).stem
        chunks = slicer.cut(wav_path, db_thresh=slice_db)
        audio_data, audio_sr = slicer.chunks2audio(wav_path, chunks)

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
                _cluster_ratio = 0.0
                if speaker["cluster_path"] != "":
                    _cluster_ratio = float(cluster_ratio_text)
                out_audio, out_sr = svc_model.infer(
                    speaker["name"], trans, raw_path,
                    cluster_infer_ratio=_cluster_ratio,
                    auto_predict_f0=isAutoPitchChecked,
                    noice_scale=float(noise_scale_text))
                _audio = out_audio.cpu().numpy()
                pad_len = int(svc_model.target_sample * 0.5)
                _audio = _audio[pad_len:-pad_len]
            audio.extend(list(infer_tool.pad_array(_audio, length)))

        res_path = os.path.join(save_path, f'{wav_name}_{trans}_key_{speaker["name"]}.wav')
        soundfile.write(res_path, audio, svc_model.target_sample, format="wav")
        print(f"Converted audio saved to {res_path}")  # Добавляем вывод сообщения о сохранении файла
        return True 