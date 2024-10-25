import argparse
import glob
import shutil
import wave
import json
import os
from utils import *

def read_json_file(file_path):
    with open(file_path, 'r', encoding="utf8") as file:
        data = json.load(file)
    return data

def round_float(number, decimal_places=2):
    factor = 10 ** decimal_places
    return round(number * factor) / factor

def get_wav_duration(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        sample_rate = wav_file.getframerate()
        num_frames = wav_file.getnframes()
        duration = num_frames / float(sample_rate)

    return duration

# Constructing data in a standard format
def build(root_path,output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Folder '{output_path}' created.")

    subfolders = [f.path for f in os.scandir(output_path) if f.is_dir()]
    count = len(subfolders) 
    folders = get_all_folders(root_path)
    data = {}

    two_step_folder = root_path+"\\two-step\\"
    sub_folders = get_all_folders(two_step_folder)     
    for sub_folder in sub_folders:
        episode = os.path.basename(sub_folder) 
        sub_sub_folders = get_all_folders(sub_folder)   
        for sub_sub_folder in sub_sub_folders:
            segment = os.path.basename(sub_sub_folder)
            audio_folders = get_all_folders(sub_sub_folder)
            audio_folder_num = int(len(audio_folders))  
            current_temp_path = None
            
            for dia_index in range(0, audio_folder_num):
                dialog_audio_path = sub_sub_folder+"\\"+str(dia_index)+"_audio"
                print(dialog_audio_path)
                # json_data = read_json_file(dialog_audio_path + "\\note.json")
                
                with open(dialog_audio_path + "\\note.json", 'r', encoding="utf-8") as file:
                    json_data = json.load(file)

                print(dia_index)
                not_none_index = 0
                first_speaker = None
                current_index = 0

                temp_output_path = os.path.join(output_path, str(count))

                print(temp_output_path)
                if not os.path.exists(temp_output_path):
                    os.makedirs(temp_output_path)
                else:
                    count += 1
                    continue

                dialog_element = {
                    'dialog': count, 
                    'utterents': {} 
                }

                for element in json_data:
                    index = element["index"]
                    source_speaker = speaker = int(element["speaker"])

                    if (current_index == 0 or not_none_index == 0):
                        first_speaker = speaker
                        speaker = 0
                    else:
                        if (speaker != first_speaker):
                            speaker = 1
                        else:
                            speaker = 0

                    source_wav_path = dialog_audio_path+"\\"+str(current_index)+"_"+str(source_speaker)+"_*_16k.wav"
                    target_wav_path = str(current_index)+"_"+str(speaker)+"_d"+str(count)+".wav"
                    new_file_path = os.path.join(temp_output_path, target_wav_path)

                    matched_files = glob.glob(source_wav_path)
                    if(len(matched_files) != 0):
                        print(matched_files[0])   
                        shutil.copy(matched_files[0], new_file_path)
                        wav_file = matched_files[0]
                    else:
                        source_wav_path = dialog_audio_path + "\\" + str(current_index) + "_" + str(
                            source_speaker) + "_*.wav"
                        matched_files = glob.glob(source_wav_path)

                        if(len(matched_files) == 0):
                            source_wav_path = dialog_audio_path + "\\" + str(current_index) + "_" + str(
                                speaker) + "_*.wav"
                            matched_files = glob.glob(source_wav_path)

                        wav_file = matched_file = matched_files[0]

                        from scipy.io import wavfile
                        import numpy as np
                        samplerate, data = wavfile.read(matched_file)
                        if len(data.shape) > 1:
                            print("Not mono!")
                            mono_data = np.mean(data, axis=1, dtype=data.dtype)
                        else:
                            mono_data = data
                        new_file_path = new_file_path
                        wavfile.write(new_file_path, samplerate, mono_data)

                    target_lab_path = str(current_index)+"_"+str(speaker)+"_d"+str(count)+".lab"
                    lab_file_path = os.path.join(temp_output_path, target_lab_path)

                    content = element["text"]
                    with open(lab_file_path, 'w',encoding="utf8") as lab_file:
                        lab_file.write(content)

                    element_data = {
                        'index': not_none_index,
                        'duration': round_float(get_wav_duration(wav_file)),
                        'speaker': speaker,
                        'text': content,
                        'sample_rate': 16000
                    }
                    dialog_element['utterents'][not_none_index] = element_data

                    not_none_index += 1
                    current_index += 1

                metadata_json_path = os.path.join(temp_output_path) + '/metadata.json'
                with open(metadata_json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(dialog_element, json_file, indent=4, ensure_ascii=False)
                json_file.close()
                count += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio_root_path', required=True, type=str)
    parser.add_argument('--result_path', required=True, type=str)
    args = parser.parse_args()
    build(args.audio_root_path, args.result_path)

# python step-6.py --audio_root_path "xxx" --result_path "yyy"

# root_path = "F:\\test\\"
# output_path = "F:\\"   # Sorted conversation data