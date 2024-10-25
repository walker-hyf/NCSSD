# NCSSD
## Introduction

This is the official repository for the NCSSD dataset and collecting pipeline to handle TV shows. [《Generative Expressive Conversational Speech Synthesis》](https://arxiv.org/pdf/2407.21491)
 (Accepted by MM'2024)

[Rui Liu *](https://ttslr.github.io/), Yifan Hu, [Yi Ren](https://rayeren.github.io/), Xiang Yin, [Haizhou Li](https://colips.org/~eleliha/).

## NCSSD Overview 
Includes Recording subsets: R-ZH, R-EN and Collection subsets: C-ZH, C-EN.
<div align=center><img width="500" height="340" src="image-1.png"/></div>

## NCSSD Download
⭐ Huggingface download address: [NCSSD](https://huggingface.co/datasets/walkerhyf/NCSSD).

⭐ Users in China can contact the email (📧: ``hyfwalker@163.com``) to obtain the Baidu Cloud address, but you need to provide necessary information such as name, organization, profession, etc.

<!-- GPT-Talker的爬取数据流程 -->

## Collection Subset Pipeline
<div align=center><img width="800" height="220" src="image.png"/></div>

<!-- 0. 搜集的视频+统一名称 -->
### 1. Video Selection
#### 1.1 Prepare TV shows and name it: **TV name-episode number**.

#### 1.2. Extract the audios from MKV videos (video_file: input video file name, output_file: output audio file name).
```
python ./step-0.py --input_video_path "xxx.mkv" --output_audio_path "xxx.wav"
```

<!-- Dialogue Scene Extraction -->
### 2. Dialogue Scene Extraction
#### 2.1 Use VAD to segment speech audio, split into two segments if the silent interval is greater than 4 seconds, and retain segments with more than 30% valid speech duration and longer than 15 seconds.
```
python ./step-1.py --audio_root_path "xxx"
```

<!-- Demucs -->
#### 2.2 Use Demucs for vocal and background separation.
##### (1) To install Demucs, you can refer to the official documentation or installation instructions provided at the following link: [https://github.com/facebookresearch/demucs](https://github.com/facebookresearch/demucs). 

##### (2) Use the Demucs mentioned above to separate vocals and background sounds, and keep the vocals part with SNR<=4.
```
python ./step-2.py --audio_root_path "xxx"
```

<!-- sepformer -->
#### 2.3 Use SepFormer for voice enhancement.
##### (1) To install SepFormer, you can refer to the official documentation or installation instructions provided at the following link: [https://huggingface.co/speechbrain/sepformer-dns4-16k-enhancement](https://huggingface.co/speechbrain/sepformer-dns4-16k-enhancement). (*vocals_16k_path* is the folder generated in a previous step, located in the **one-step** directory.)
```
python ./step-3.py --vocals_16k_path "yyy"
```

<!-- Speaker -->
### 3. Dialogue Segment Extraction
We use the [Volcengine](https://console.volcengine.com/speech/app) for speaker recognition, extracting different conversation scenes. Please configure ASR information such as ``appid``,``token``, and OSS information such as ``access_key_id``,``access_key_secret``,``bucket_name`` (for generating URLs to be used for ASR)
```
python ./step-4.py --audio_root_path "xxx"
```



### 4. Dialogue Script Recognition
#### Use Aliyun's ASR service for re-recognition and correction.

We use the [Aliyun's ASR](https://ai.aliyun.com/nls/filetrans?spm=5176.28508143.nav-v2-dropdown-menu-0.d_main_9_1_1_1.5421154aIHmaWo&scm=20140722.X_data-b7a761a1c730419a6c79._.V_1) for dialogue script recognition. Please configure ASR information such as ``accessKeyId``,``accessKeySecret``, and OSS information such as ``access_key_id``,``access_key_secret``,``bucket_name`` (for generating URLs to be used for ASR). 

⚠ ``appkey``: Pay attention to the Chinese and English settings.

```
python ./step-5.py --audio_root_path "xxx"
```


### 5. Organizing the Data
Organize the data from the above steps into a standard format, with *result_path* as the output result path.
```
python step-6.py --audio_root_path "xxx" --result_path "yyy"
```


🎉🎉🎉 ***Congratulations! The dataset was created successfully!***

## Citations

```bibtex
@inproceedings{
liu2024generative,
    title={Generative Expressive Conversational Speech Synthesis},
    author={Rui Liu and Yifan Hu and Yi Ren and Xiang Yin and Haizhou Li},
    booktitle={ACM Multimedia 2024},
    year={2024},
    url={https://openreview.net/forum?id=eK9ShhDqwu}
}
```


⚠ The collected TV shows clips are all from public resources on the Internet. If there is any infringement, please contact us to delete them. (📧: ``hyfwalker@163.com``)






