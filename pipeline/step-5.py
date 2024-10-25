# -*- coding: utf8 -*-
import argparse
import datetime
import glob
import json
import os
import time
from urllib.parse import quote
import oss2
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from utils import *


def read_json_file(file_path):
    with open(file_path, 'r',encoding="utf8") as file:
        data = json.load(file)
    return data


# Convert all wav files in the folder to the specified format
def convert_wav_files(folder_path):
    for file_name in os.listdir(folder_path):
        if(file_name.endswith("_background.wav") or file_name.endswith("_vocals.wav") or file_name.endswith("_vocals_16k.wav")
            or file_name.endswith("_background_16k.wav")):
            os.remove(folder_path+"\\"+file_name)

        if file_name.endswith(".wav") and not file_name.endswith("_16k.wav"):
            input_file = os.path.join(folder_path, file_name)
            file_name_without_extension = os.path.splitext(file_name)[0]
            output_file = os.path.join(folder_path, file_name_without_extension+"_16k.wav")

            if(os.path.exists(output_file)):
                pass
            else:
                # 使用FFmpeg进行音频转换，自动覆盖原始文件
                ffmpeg_cmd = f'ffmpeg -i "{input_file}" -ac 1 -ar 16000 -sample_fmt s16 "{output_file}"'
                subprocess.call(ffmpeg_cmd, shell=True)

def fileTrans(akId, akSecret, appKey, fileLink) :
    REGION_ID = "cn-shanghai"
    PRODUCT = "nls-filetrans"
    DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
    API_VERSION = "2018-08-17"
    POST_REQUEST_ACTION = "SubmitTask"
    GET_REQUEST_ACTION = "GetTaskResult"
    KEY_APP_KEY = "appkey"
    KEY_FILE_LINK = "file_link"
    KEY_VERSION = "version"
    KEY_ENABLE_WORDS = "enable_words"
    KEY_AUTO_SPLIT = "auto_split"
    KEY_TASK = "Task"
    KEY_TASK_ID = "TaskId"
    KEY_STATUS_TEXT = "StatusText"
    KEY_RESULT = "Result"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_RUNNING = "RUNNING"
    STATUS_QUEUEING = "QUEUEING"
    client = AcsClient(akId, akSecret, REGION_ID)
    postRequest = CommonRequest()
    postRequest.set_domain(DOMAIN)
    postRequest.set_version(API_VERSION)
    postRequest.set_product(PRODUCT)
    postRequest.set_action_name(POST_REQUEST_ACTION)
    postRequest.set_method('POST')
    task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False}
    task = json.dumps(task)
    print(task)
    postRequest.add_body_params(KEY_TASK, task)
    taskId = ""

    try:
        postResponse = client.do_action_with_exception(postRequest)
        postResponse = json.loads(postResponse)
        print(postResponse)
        statusText = postResponse[KEY_STATUS_TEXT]
        if statusText == STATUS_SUCCESS:
            print("The recording file recognition request was successfully responded!")
            taskId = postResponse[KEY_TASK_ID]
        else:
            print("Recording file recognition request failed!")
            return

    except ServerException as e:
        print (e)
    except ClientException as e:
        print (e)
    getRequest = CommonRequest()
    getRequest.set_domain(DOMAIN)
    getRequest.set_version(API_VERSION)
    getRequest.set_product(PRODUCT)
    getRequest.set_action_name(GET_REQUEST_ACTION)
    getRequest.set_method('GET')
    getRequest.add_query_param(KEY_TASK_ID, taskId)

    statusText = ""
    while True :
        try :
            getResponse = client.do_action_with_exception(getRequest)
            getResponse = json.loads(getResponse)
            print(getResponse)
            for i in getResponse:
                if(i == "Result"):
                    result = getResponse[i]["Sentences"]
                    result_text = ""
                    emotion_value = 0
                    num = 0
                    for tem in result:
                        print(tem)
                        num += 1
                        result_text += tem["Text"]
                        emotion_value += tem["EmotionValue"]
                    emotion_value = emotion_value/num
                    return result_text, str(emotion_value)   

            statusText = getResponse[KEY_STATUS_TEXT]
            if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING :
                time.sleep(10)
            else:
                break
        except ServerException as e:
            print(e)
        except ClientException as e:
            print(e)
    if statusText == STATUS_SUCCESS:
        print ("The recording file was recognized successfully!")
    else :
        print ("Recording file recognition failed!")
        return "", str(0)
    return

def save_text_as_lab(text, filename):
    with open(filename, 'w') as file:
        file.write(text)

def remove_file_extension(file_path):
    file_name = os.path.basename(file_path)
    file_name_without_extension = os.path.splitext(file_name)[0]
    directory = os.path.dirname(file_path)
    file_path_without_extension = os.path.join(directory, file_name_without_extension)
    return file_path_without_extension

# Alibaba ASR Configuration
accessKeyId = 'xxx'
accessKeySecret = 'xxx'
appkey = 'xxx'   # EN or ZH

# Upload files to OSS
access_key_id = 'xxx'
access_key_secret = 'xxx'
endpoint = 'https://oss-cn-beijing.aliyuncs.com' 
bucket_name = 'xxx'

# Use Alibaba's ASR to re-recognize the segmented audio
def ali_asr(root_folder):
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    start = datetime.datetime.now()

    input_dir = root_folder + "\\two-step\\"
    sub_folders = get_all_folders(input_dir) 
    for sub_sub_folder in sub_folders:
        sub_sub_folders = get_all_folders(sub_sub_folder)
        for sub_sub_folder in sub_sub_folders:
            sub_sub_sub_folders = get_all_folders(sub_sub_folder)
            for sub_sub_sub_folder in sub_sub_sub_folders:
                if(sub_sub_sub_folder.endswith("_audio")):
                    convert_wav_files(sub_sub_sub_folder)
                    wav_files = glob.glob(os.path.join(sub_sub_sub_folder + "\\", "*_16k.wav"))
                    json_data = read_json_file(sub_sub_sub_folder + "\\note.json")

                    for wav_file_path in wav_files:
                        print(wav_file_path)
                        wav_file = os.path.basename(wav_file_path)
                        oss_path = wav_file 
                        with open(wav_file_path, 'rb') as file:
                            try:
                                file_path = remove_file_extension(wav_file_path)
                                lab_filename = file_path + ".lab"
                                if(os.path.exists(lab_filename)):
                                    continue
                                else:
                                    oss_path = oss_path.replace("！", "")
                                    bucket.put_object(oss_path, file)
                                    encoded_oss_path = quote(oss_path, safe='/')
                                    oss_file_url = bucket.sign_url('GET', encoded_oss_path, 5 * 60, slash_safe=True)

                                    print('Path to upload audio files:', oss_file_url)
                                    audio_url = oss_file_url
                                    time.sleep(5)
                                    fileLink = audio_url
                                    result, emotion_value = fileTrans(accessKeyId, accessKeySecret, appkey, fileLink)
                                    print("The result of the recognition is:"+result)
                                    print("Emotional intensity is:"+emotion_value)

                                    save_text_as_lab(result, lab_filename)

                                    index = wav_file.split("_")[0]
                                    json_data[int(index)]['text'] = result
                                    json_data[int(index)]['emotion_value'] = emotion_value
                                    print(json_data)

                            except Exception as e:
                                print("//////////////////")
                                print(e)
                                return

                    with open(sub_sub_sub_folder+"\\note.json", 'w', encoding='utf-8') as json_file:
                        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio_root_path', required=True, type=str)
    args = parser.parse_args()
    ali_asr(args.audio_root_path)

# python step-5.py --audio_root_path "xx"
# appkey: Pay attention to the Chinese and English settings

