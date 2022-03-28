import os
import json
import requests


def send_request(url, audio, transcript):
    audio_name = os.path.basename(audio)
    if os.path.isfile(transcript):
        with open(transcript, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = transcript

    params_obj = {"fname": audio_name, "transcript": text}

    payload = {
        "type": "audio",
        "format": "LINEAR16",
        "sampleRate": 16000,
        "params": params_obj
    }
    files = {
        'request': (None, json.dumps(payload), 'application/json'),
        'content': (os.path.basename(audio), open(audio, 'rb'), 'audio/x-wav')
    }

    r = requests.post(url, files=files).json()
    print(json.dumps(r, indent=4, ensure_ascii=False))


send_request(url='http://localhost:8000/process/fi',
             audio='src_for_wav/pohjantuuli_ja_aurinko.wav',
             transcript='src_for_txt/pohjantuuli_ja_aurinko.txt')

send_request(url='http://localhost:8000/process/fi',
             audio='ikkuna.wav',
             transcript='ikkuna')
