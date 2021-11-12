import os
import numpy as np
from datetime import datetime
import wave
import pyaudio
from deepspeech import Model, version
from google.api_core.exceptions import AlreadyExists
from google.cloud import texttospeech
import json
import html
import io
from playsound import playsound
from google.cloud import speech

import tkinter as tk
import time
from tkinter import scrolledtext
import socket
import threading
from datetime import datetime

# set the variable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key.json'

# https://blog.csdn.net/LiePy/article/details/105037104
"""pyaudio参数"""
CHUNK = 1024  # 数据包或者数据片段
FORMAT = pyaudio.paInt16  # pyaudio.paInt16表示我们使用量化位数 16位来进行录音
CHANNELS = 1  # 声道，1为单声道，2为双声道
RATE = 16000  # 采样率，每秒钟16000次
WAVE_OUTPUT_FILENAME = 'tmp.wav'
count = 0
from pynput.keyboard import Listener
import threading

# RECORD_SECONDS = 5  # 录音时间
run = False

t2s_client = texttospeech.TextToSpeechClient()  # systhenis client
s2t_client = speech.SpeechClient()


def recoder():
    print('start recording')
    _frames = []
    p = pyaudio.PyAudio()
    global run
    stream = p.open(channels=CHANNELS,
                    format=FORMAT,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    while run:
        data = stream.read(CHUNK)
        _frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(_frames))
    wf.close()


def press(key):
    global run
    try:
        # print(str(key))
        if str(key) == 'Key.space':
            run = not run
            # print('run change', run)
    except AttributeError as e1:
        print(e1)
        pass


def check_input():
    with Listener(on_press=press) as listener:
        listener.join()


def text_to_speech(client, text, outfile):
    # Instantiates a client

    # Set the text input to be synthesized
    # clinet = client
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(outfile, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        # print('Audio content written to file "output.mp3"')


def speech_to_text(client):
    gs_order = 'gsutil cp tmp.wav gs://deepspeech_bucket'
    os.system(gs_order)
    gcs_uri = "gs://deepspeech_bucket/tmp.wav"
    ans = ''
    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))
        ans += result.alternatives[0].transcript
    return ans


def show_info(str, agent):
    now = datetime.now()
    s_time = now.strftime("%Y-%m-%d %H:%M:%S")
    str = str.rstrip()
    if len(str) == 0:
        return -1
    temp = agent + '\t' + s_time + "\n    " + str + "\n"
    t1_Msg.insert(tk.INSERT, "%s" % temp)


def test():
    global run
    ds = Model('deepspeech-0.9.3-models.pbmm')
    ds.enableExternalScorer('deepspeech-0.9.3-models.scorer')
    global count
    while 1:
        if run:
            recoder()
            count += 1
            # file = 'tmp.wav'
            # fin = wave.open(file, 'rb')
            # audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)
            # fin.close()
            # infered_text = ds.stt(audio)
            # infered_text = speech_to_text(s2t_client)
            # time.sleep(2)
            order = 'deepspeech --model deepspeech-0.9.3-models.pbmm --scorer deepspeech-0.9.3-models.scorer --audio tmp.wav'
            s = os.popen(order)
            infered_text = s.read()
            print(infered_text)
            show_info(infered_text, 'Me')
            out_text = 'text:' + infered_text + '\t' + 'labels: Good'
            with open('tmp.txt', 'w') as f:
                f.write(out_text)
            parlai_order = 'python ParlAI/parlai/scripts/eval_model.py --task fromfile:parlaiformat --fromfile_datapath tmp.txt  --model-file zoo:blender/blender_90M/model --world-logs out.txt '
            os.system(parlai_order)
            with open('out.jsonl', 'r') as f:
                json_dict = json.load(f)
                try:
                    response = json_dict['dialog'][0][1]['text']
                except:
                    response = " "
                if infered_text == 'Say goodbye to everyone':
                    response = 'Goodbye Everyone! Hope you have a nice day.'
                print(response)

                show_info(response, 'Zoe')
                text_to_speech(t2s_client, response, 'tmp_out.mp3')
                playsound('tmp_out.mp3')


if __name__ == '__main__':
    prologue = "Hi I'm Zoe!"
    print(prologue)

    app = tk.Tk()
    app.title('与python聊天')

    w = 800
    h = 660
    sw = app.winfo_screenwidth()
    sh = app.winfo_screenheight()
    x = 200
    y = (sh - h) / 2
    app.geometry("%dx%d+%d+%d" % (w, h, x, y))
    app.resizable(0, 0)
    t1_Msg = tk.Text(width=113, height=35)
    t1_Msg.tag_config('green', foreground='#008C00')  # 创建tag
    t1_Msg.place(x=2, y=35)
    show_info("Hi I'm Zoe", 'Zoe')
    t1 = threading.Thread(target=check_input, args=())
    t1.start()
    t2 = threading.Thread(target=test, args=())
    t2.start()
    app.mainloop()
