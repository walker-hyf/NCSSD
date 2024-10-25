import argparse
import datetime
import glob
import os
import wave
import torch
import demucs.api
import demucs.separate
import librosa
import numpy as np
from speechbrain.inference.separation import SepformerSeparation as separator
from utils import *

# Speech resampling
def resample_audio(input_file, output_file, target_sample_rate):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-ar', str(target_sample_rate),
        output_file
    ]
    subprocess.run(command)

# Separating vocals and background sounds using demucs.
def demucs_samplerate(root_folder):
    folders = get_all_folders(root_folder+"\\one-step\\")
    print(folders)
    
    for subfolder in folders:
        wav_files = glob.glob(os.path.join(subfolder+"\\", "*.wav"))
        print("Starting separation task...")
        for wav_path in wav_files:
            wav_file = os.path.basename(wav_path)
            file_name_without_extension = os.path.splitext(wav_file)[0]
            wav_file = file_name_without_extension+".wav"
            wav_path = os.path.join(subfolder, wav_file) 
            print("Separating:"+wav_path)
            if(not file_name_without_extension.endswith("_vocals")
                and not file_name_without_extension.endswith("_background")
                and not file_name_without_extension.endswith("_vocals_16k")
                and not file_name_without_extension.endswith("_background_16k")
            ):
                background_path = os.path.join(subfolder, file_name_without_extension+"_background.wav")
                vocals_path = os.path.join(subfolder, file_name_without_extension + "_vocals.wav")
                if(os.path.exists(background_path) and os.path.exists(vocals_path)):
                    pass
                else:
                    separator = demucs.api.Separator(model="mdx_extra", segment=12)
                    origin, separated = separator.separate_audio_file(wav_path)
                    os.makedirs(subfolder, exist_ok=True)

                    other = drums = bass = None
                    for item in separated:
                        if (item == "vocals"):
                            demucs.api.save_audio(separated[item], f"{subfolder}/{file_name_without_extension}_vocals.wav",
                                                samplerate=separator.samplerate)
                        elif(item == "drums"):
                            drums = separated[item]
                        elif(item == "bass"):
                            bass = separated[item]
                        elif(item == "other"):
                            other = separated[item]

                    no_vocals = torch.add(drums,bass)
                    no_vocals = torch.add(no_vocals,other)
                    demucs.api.save_audio(no_vocals, f"{subfolder}/{file_name_without_extension}_background.wav",
                                            samplerate=separator.samplerate)

                man_wav_path = f"{subfolder}/{file_name_without_extension}_vocals.wav"
                background_wav_path = f"{subfolder}/{file_name_without_extension}_background.wav"

                man_audio, _ = librosa.load(man_wav_path, sr=None)
                background_audio, _ = librosa.load(background_wav_path, sr=None)

                snr = 10 * np.log10(np.mean(man_audio ** 2) / np.mean(background_audio ** 2))

                if(snr <= 4):
                    if os.path.exists(man_wav_path):
                        os.remove(man_wav_path)
                        print("Deleted successfully: "+man_wav_path)
                    if os.path.exists(background_wav_path):
                        os.remove(background_wav_path)
                        print("Deleted successfully: " + background_wav_path)
                else:
                    vocals_16k_path = os.path.join(subfolder, file_name_without_extension + "_vocals_16k.wav")
                    if(os.path.exists(vocals_16k_path)):
                        pass
                    else:
                        with wave.open(man_wav_path, 'rb') as audio_file:
                            sample_rate = audio_file.getframerate()
                            converted_file = f"{subfolder}/{file_name_without_extension}_vocals_16k.wav"
                            if sample_rate != 16000:
                                target_sample_rate = 16000
                                resample_audio(man_wav_path, converted_file, target_sample_rate)

                print("Finish.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio_root_path', required=True, type=str)
    args = parser.parse_args()
    demucs_samplerate(args.one_step_path)

#  python step-2.py --audio_root_path "xxx"