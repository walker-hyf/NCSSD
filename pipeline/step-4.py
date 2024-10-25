
import argparse
import datetime
import glob
import os
from urllib.parse import quote
import oss2
import requests
import json
import time
import soundfile
from utils import *
from moviepy.editor import VideoFileClip

s = requests.session()
s.keep_alive = False

def submit_task(appid, token, cluster, audio_url, service_url, headers):
    request = {
        "app": {
            "appid": appid,
            "token": token,
            "cluster": cluster
        },
        "user": {
            "uid": "388808087185088_demo"
        },
        "audio": {
            "format": "wav",
            "url": audio_url
        },
        "additions": {
            'with_speaker_info': 'True',
        }
    }

    r = s.post(service_url + '/submit', data=json.dumps(request), headers=headers)
    # print(r)
    if(r.text==None or r.text=="" ):
        return None
    else:
        resp_dic = json.loads(r.text)
        print(resp_dic)
        id = resp_dic['resp']['id']
        # print(id)
        return id

def query_task(task_id):
    query_dic = {}
    query_dic['appid'] = appid
    query_dic['token'] = token
    query_dic['id'] = task_id
    query_dic['cluster'] = cluster
    query_req = json.dumps(query_dic)
    # print(query_req)
    r = s.post(service_url + '/query', data=query_req, headers=headers)
    # print(r.text)
    if(r.text == None or r.text == ""):
        return None
    else:
        resp_dic = json.loads(r.text)
        return resp_dic

def file_recognize(appid, token, cluster, audio_url, service_url, headers):
    task_id = submit_task(appid, token, cluster, audio_url, service_url, headers)
    if(task_id == None):
        return None
    start_time = time.time()
    while True:
        time.sleep(2)
        resp_dic = query_task(task_id)
        if resp_dic['resp']['code'] == 1000:  # task finished
            print("ASR result was obtained successfully.")

            merge_result = []        
            flag = False             
            comma_flag = False       
            split_result = []        
            count_flag = True

            old_speaker = old_text = old_start_time = old_end_time = None
            for element in resp_dic['resp']['utterances']:

                if(count_flag == True):
                    old_speaker = element['additions']['speaker']  
                    old_text = element['text'].strip()             
                    old_start_time = element['start_time']        
                    old_end_time = element['end_time']            
                    count_flag = False
                else:
                    current_speaker = element['additions']['speaker'] 
                    current_text = element['text'].strip()  
                    current_start_time = element['start_time'] 
                    current_end_time = element['end_time']  

                    if (current_speaker == old_speaker):
                        if(old_text == ""):
                            old_start_time = current_start_time

                        old_end_time = current_end_time
                        old_text += current_text


                        last_character = element['text'].strip()[-1]
                        if (has_chinese_punctuation(last_character) and last_character != "," and last_character != "，"):
                            merge_result.append([current_speaker, old_start_time, old_end_time, old_text])
                            old_text = ""
                            # old_start_time = current_start_time 

                        else:
                            old_speaker = current_speaker    
                            old_end_time = current_end_time 

                    else:
                        if(old_text != ""):
                            merge_result.append([old_speaker, old_start_time, old_end_time, old_text])
                        old_speaker = current_speaker  
                        old_text = current_text 
                        old_start_time = current_start_time  
                        old_end_time = current_end_time  

            if (count_flag == True):
                print("The current conversation has only one utterance")
                merge_result.append([old_speaker, old_start_time, old_end_time, old_text])

            speaker_result = set()  
            dialogue_temp = []     
            old_speaker_result = set()

            for index, element_re in enumerate(merge_result):
                if(index == len(merge_result)-1):
                    old_speaker_result = speaker_result.copy()
                    speaker_result.add(str(element_re[0]))
                    if(len(speaker_result) > 2):
                        pass
                    else:
                        dialogue_temp.append(element_re)

                    speaker_A = 0 
                    speaker_B = 0 
                    old_speaker_result = list(old_speaker_result)
                    for tem_index,tem in enumerate(dialogue_temp):

                        if (len(old_speaker_result) <= 1):
                            print("The dialogue turns does not meet the requirements")
                            return None

                        if (old_speaker_result[0] == tem[0]):
                            speaker_A += 1
                            dialogue_temp[tem_index][0] = "0"   

                        elif (old_speaker_result[1] == tem[0]):
                            speaker_B += 1
                            dialogue_temp[tem_index][0] = "1"  

                    if (speaker_A <= 2 or speaker_B <= 2):
                        print("One of the speakers has less than 2 utterances")
                        pass
                    else:
                        split_result.append(dialogue_temp)

                else:
                    old_speaker_result = speaker_result.copy()
                    speaker_result.add(str(element_re[0]))
                    if(len(speaker_result) > 2):
                        speaker_A = 0   
                        speaker_B = 0  
                        old_speaker_result = list(old_speaker_result)

                        for tem_index, tem in enumerate(dialogue_temp):
                            if(old_speaker_result[0] == tem[0]):
                                speaker_A += 1
                                dialogue_temp[tem_index][0] = "0"  
                            elif(old_speaker_result[1] == tem[0]):
                                speaker_B += 1
                                dialogue_temp[tem_index][0] = "1"  

                        if(speaker_A<=2 or speaker_B<=2):
                            print("One of the speakers has less than 2 utterances")
                            pass
                        else:
                            split_result.append(dialogue_temp)

                        speaker_result = set() 
                        old_speaker_result = set()
                        dialogue_temp = []
                        speaker_result.add(str(element_re[0]))

                    dialogue_temp.append(element_re)

            return split_result

        elif resp_dic['resp']['code'] < 2000: # task failed
            print("failed")
            exit(0)
        now_time = time.time()
        if now_time - start_time > 300: # wait time exceeds 300s
            print('wait time exceeds 300s')
            exit(0)

# Split a single audio
def split_audio(segment_start_time, index, speaker, wav, sr, output_dir, start_time, end_time):

    start_time_temp = int(start_time / 1000 * sr)
    end_time_temp = int(end_time / 1000 * sr)
    speech_segment = wav[start_time_temp:end_time_temp]

    output_file = os.path.join(output_dir, f"{index}_{speaker}_{(segment_start_time+start_time)/1000}_{(segment_start_time+end_time)/1000}.wav")

    soundfile.write(output_file, speech_segment, sr) 

    print(f'Audio: {str(datetime.timedelta(seconds=(segment_start_time+start_time)/1000))} - {str(datetime.timedelta(seconds=(segment_start_time+end_time)/1000))} saved as {output_file}')

    print(f"Splitting is successful: {output_file}")

# Split all audio
def split_audio_files(segment_start_time, segment_name, count, input_file, output_dir, dialogue_temp):
    output_dir = os.path.join(output_dir, segment_name+"/"+str(count) + "_audio/")
    os.makedirs(output_dir, exist_ok=True)
    wav, sr = soundfile.read(input_file, dtype='float32')
    data = []          
    for index, segment in enumerate(dialogue_temp):
        speaker = segment[0]
        start_time = segment[1]   
        end_time = segment[2]    
        text = segment[3]
        element_data = {
            'segment_name': segment_name,
            'start_time': (segment_start_time+start_time)/1000,
            'end_time': (segment_start_time+end_time)/1000,
            'speaker': speaker,
            'text': text,
            'count': count,
            'index': index,
            'type': "wav",
        }

        data.append(element_data)
        split_audio(segment_start_time, index, speaker, wav, sr, output_dir, start_time, end_time)

    with open(output_dir+'/note.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)


# According to the timestamp results of ASR, audio segmentation is performed
def asr_split_function(input_dir, segment_name,appid, token, cluster, audio_url, service_url, headers, input_wav, output_dir):
    result = file_recognize(appid, token, cluster, audio_url, service_url, headers)
    if(result == None):
        return None
    if(result != None and result != []):
        for count, re in enumerate(result):
            if(re != []):
                tv_name_number = os.path.basename(input_wav).split(".")[0].split("_")[0]
                tv_number = tv_name_number.split("-")[1] 

                pattern = input_dir + "\\" + tv_number + "\\" + tv_name_number + "_" + segment_name + "*_vocals.wav"
                matching_files = glob.glob(pattern)
                vad_vocals_path = ""
                for file_path in matching_files:
                    vad_vocals_path = file_path
                    break

                segment_start_time = round(float(os.path.basename(vad_vocals_path).split("_")[2])*1000,2)
                split_audio_files(segment_start_time, segment_name, count, input_wav, output_dir, re)

    else:
        print("Finish.")

# zh_ASR api
appid = 'xxx'
token = 'xxx'
cluster = 'volc_auc_video'
service_url = 'https://openspeech.bytedance.com/api/v1/auc'
headers = {'Authorization': 'Bearer; {}'.format(token)}


# Upload files to OSS
access_key_id = 'xxx'
access_key_secret = 'xxx'
endpoint = 'https://oss-cn-beijing.aliyuncs.com'
bucket_name = 'xxx'

# Upload the audio file to OSS, then perform ASR and spliting tasks
def asr_split(root_folder):
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    start = datetime.datetime.now()
    
    input_dir = root_folder + "\\one-step\\"
    output_dir = root_folder + "\\two-step\\"
    sub_folders = get_all_folders(input_dir)
    for sub_folder in sub_folders:
        wav_files = glob.glob(os.path.join(sub_folder, "*.wav"))
        vocals_files = [file for file in wav_files if os.path.basename(file).endswith("_enhanced.wav")]
        for wav_path in vocals_files:
            input_wav = wav_path
            wav_file = os.path.basename(wav_path)
            # file_name_without_extension = os.path.splitext(wav_file)[0]

            # local_file_path = wav_file
            oss_file_name = wav_file
            # tv_name = wav_file.split("_")[0]
            segment_name = str(wav_file.split("_")[1])
            oss_path = oss_file_name
            time.sleep(2)

            with open(wav_path, 'rb') as file:
                try:
                    oss_path = oss_path.replace("！", "")
                    bucket.put_object(oss_path, file)
                    encoded_oss_path = quote(oss_path, safe='/')
                    oss_file_url = bucket.sign_url('GET', encoded_oss_path, 5 * 60, slash_safe=True)
                    print('Path to upload audio files:', oss_file_url)
                    audio_url = oss_file_url
                    time.sleep(5)

                    output_dir_temp = output_dir + str(sub_folder.split("\\")[-1])
                    asr_split_function(input_dir, segment_name, appid, token, cluster, audio_url,
                                        service_url, headers, input_wav, output_dir_temp)

                except Exception as e:
                    print("//////////////////")
                    print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio_root_path', required=True, type=str)
    args = parser.parse_args()
    asr_split(args.audio_root_path)


# python step-4.py --audio_root_path "xx"



