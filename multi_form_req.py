import os
import json
import requests


def send_request(url, audio, transcript):
    audio_name = os.path.basename(audio)
    with open(transcript, 'r', encoding='utf-8') as f:
        text = f.read()

    script = {"fname": audio_name, "transcript": text}
    payload = {
        "type": "audio",
        "format": "LINEAR16",
        "sampleRate": 16000,
        "features": script
    }
    files = {
        'request': (None, json.dumps(payload), 'application/json'),
        'content': (os.path.basename(audio), open(audio, 'rb'), 'audio/x-wav')
    }

    r = requests.post(url, files=files).json()
    print(json.dumps(r, indent=4, ensure_ascii=False))


for i in range(1):
    send_request(url='http://localhost:8000/process',
                 audio='src_for_wav/pohjantuuli_ja_aurinko.wav',
                 transcript='src_for_txt/pohjantuuli_ja_aurinko.txt')
