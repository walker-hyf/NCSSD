import argparse
import subprocess
from utils import *

# Extract audio from video
def convert_mkv_to_wav(video_file, output_file):
    subprocess.call(['ffmpeg', '-i', video_file, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', output_file])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_video_path', required=True, type=str)
    parser.add_argument("--output_audio_path", required=True, type=str)
    args = parser.parse_args()

    convert_mkv_to_wav(args.input_video_path, args.output_audio_path)


# python step-0.py --input_video_path "xxx.mkv" --output_audio_path "xxx.wav"