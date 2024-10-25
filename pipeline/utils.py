import os
import re
import string
import subprocess

from moviepy.video.io.VideoFileClip import VideoFileClip


# Get the paths of all files in a folder
def get_file_paths(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths

# Get all subfolders under a folder
def get_all_folders(path):
    folder_paths = []
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            folder_path = os.path.join(root, dir)
            folder_paths.append(folder_path)
    return folder_paths

# Modify the file name
def rename_mkv_files(folder_path, new_name):
    for file in os.listdir(folder_path):
        if file.endswith(".mkv"):
            file_path = os.path.join(folder_path, file)
            new_file_name = os.path.join(folder_path, new_name + ".mkv")
            os.rename(file_path, new_file_name)

# Get the subfolder path under a folder
def get_subdirectories(folder_path):
    subdirectories = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            subdirectories.append(item_path)

    return subdirectories

# Determine whether there is Chinese punctuation at the end of the string
def has_chinese_punctuation(text):
    pattern = r"[\u3000-\u303F\uff01-\uff20\uff3B-\uff40\uff5B-\uff65]$"
    match = re.search(pattern, text)
    if match:
        return True
    else:
        return False

# Check if there is punctuation at the end of a string
def has_punctuation(text):
    if len(text) > 0 and text[-1] in string.punctuation:
        return True
    else:
        return False

# Get the duration of the video
def get_video_duration(file_path):
    video = VideoFileClip(file_path)
    duration = video.duration
    video.close()
    return duration

# Convert mp4 to mkv format
def convert_mp4_to_mkv(input_file, output_file):
    ffmpeg_cmd = f'ffmpeg -i "{input_file}" -codec copy "{output_file}"'
    subprocess.call(ffmpeg_cmd, shell=True)




