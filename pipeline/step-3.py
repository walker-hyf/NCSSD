import argparse
import glob
from speechbrain.inference.separation import SepformerSeparation as separator
import torchaudio
from utils import *
import wave
from pydub import AudioSegment
model = separator.from_hparams(source="speechbrain/sepformer-dns4-16k-enhancement", savedir='pretrained_models/sepformer-dns4-16k-enhancement')

def resample_audio(input_file, output_file, target_sample_rate):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-ar', str(target_sample_rate),
        output_file
    ]
    subprocess.run(command)

# Perform speech enhancement
def enhance_vocals(root_folder):
    wav_files = glob.glob(os.path.join(root_folder+"\\", "*_16k.wav"))
    print(wav_files)
    for wav_path in wav_files:
        print("Enhancing:"+wav_path)
        wav_name = os.path.basename(wav_path)
        file_name_without_extension = os.path.splitext(wav_name)[0]
        with wave.open(wav_path, 'rb') as audio_file:
            sample_rate = audio_file.getframerate()
            if sample_rate != 16000:
                print("The sampling rate is not 16k")
            else:
                est_sources = model.separate_file(path=wav_path)
                torchaudio.save(root_folder+"\\"+file_name_without_extension+"_enhanced.wav", est_sources[:, :, 0].detach().cpu(), 16000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--vocals_16k_path', required=True, type=str)
    args = parser.parse_args()
    enhance_vocals(args.vocals_16k_path)


# python step-3.py --vocals_16k_path "xx"