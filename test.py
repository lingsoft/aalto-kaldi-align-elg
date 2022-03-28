import unittest
import json
import requests
import os
import time


class TestResponseStucture(unittest.TestCase):
    base_url = 'http://localhost:8000/process/fi'
    audio = 'ikkuna.wav'
    text = 'ikkuna'
    script = {"transcript": text}

    payload = {
        "type": "audio",
        "format": "LINEAR16",
        "sampleRate": 16000,
        "params": script
    }

    files = {
        'request': (None, json.dumps(payload), 'application/json'),
        'content': (os.path.basename(audio), open(audio, 'rb'), 'audio/x-wav')
    }

    def test_api_response_status_code(self):
        """Should return status code 200
        """

        status_code = requests.post(self.base_url,
                                    files=self.files).status_code
        self.assertEqual(status_code, 200)
        time.sleep(10)

    def test_api_response_result(self):
        """Should return ELG annotation response with correct aligned
        """

        response = requests.post(self.base_url, files=self.files).json()

        self.assertEqual(response['response'].get('type'), 'annotations')
        self.assertEqual(
            response['response']['annotations']['forced_alignment'][0]
            ['features'].get('aligned'), self.text)
        self.assertEqual(
            response['response']['annotations']['forced_alignment'][0].get(
                'start'), 0.04)
        self.assertEqual(
            response['response']['annotations']['forced_alignment'][0].get(
                'end'), 0.64)
        time.sleep(10)

    def test_api_response_too_small_audio_request(self):
        """Service should return ELG failure when too small audio file is sent
        """

        too_short_audio = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\
            \x00\x01\x00\x00\x04\x00\x00\x00\x04\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00'

        local_files = {
            'request': (None, json.dumps(self.payload), 'application/json'),
            'content': ('too_short', too_short_audio, 'audio/x-wav')
        }

        response = requests.post(self.base_url, files=local_files).json()
        print(response)
        self.assertIn('failure', response)
        time.sleep(10)

    def test_api_response_invalid_audio_format_request(self):
        """Service should return ELG failure when mp3 audio file is sent
        """

        mp3_audio = 'ikkuna.mp3'

        local_files = {
            'request': (None, json.dumps(self.payload), 'application/json'),
            'content': (os.path.basename(mp3_audio), open(mp3_audio,
                                                          'rb'), 'audio/mpeg')
        }

        response = requests.post(self.base_url, files=local_files).json()
        self.assertIn('failure', response)
        time.sleep(10)


if __name__ == '__main__':
    unittest.main()
