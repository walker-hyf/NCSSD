import argparse
import datetime
import os
import soundfile
from ppasr.infer_utils.vad_predictor import VADPredictor
from utils import *

# Using VAD to split audio
def vad_split_function(tv_name, input_wav, output_dir):
    vad_predictor = VADPredictor()
    wav, sr = soundfile.read(input_wav, dtype='float32')
    speech_timestamps = vad_predictor.get_speech_timestamps(wav, sr)
    os.makedirs(output_dir, exist_ok=True)

    previous_time = 0  
    start_sample = 0   
    count = 0 
    valid_time = 0    
    mute_interval = 4

    for index, item in enumerate(speech_timestamps):
        start_time = item["start"]
        end_time = item["end"]

        # Record the time interval between the current segment and the previous segment
        temp_time = start_time/sr - previous_time  

        if temp_time > mute_interval and previous_time != 0:
            end_sample = previous_time * sr
        
            # The percentage of speaking time is greater than 30%, and the effective speaking time is greater than 15 seconds
            if(valid_time/(end_sample-start_sample)>0.3 and valid_time/sr>15):
                start_time_temp = int(start_sample)
                end_time_temp = int(end_sample)
                speech_segment = wav[start_time_temp:end_time_temp]
                output_path = os.path.join(output_dir,f'{tv_name}_{index}_{start_sample/sr}_{end_sample/sr}.wav')
                soundfile.write(output_path, speech_segment, sr)

            start_sample = start_time
            count = 0
            valid_time = 0
        else:
            count += 1
            valid_time += (end_time - start_time)

        previous_time = end_time/sr              


def vad_split(root_folder):
    for file_name in os.listdir(root_folder):
        file_path = os.path.join(root_folder, file_name)

        if(file_path.endswith(".wav")):
            input_wav = file_path
            tv_name = os.path.basename(file_path).split(".")[0]
            output_wav = root_folder + "\\one-step\\" + str(tv_name.split("-")[-1])
            vad_split_function(tv_name, input_wav, output_wav)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio_root_path', required=True, type=str)
    args = parser.parse_args()
    vad_split(args.audio_root_path)


# python step-1.py --audio_root_path "xx"



