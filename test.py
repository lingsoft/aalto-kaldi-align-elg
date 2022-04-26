import unittest
import json
import requests
import os
import time


class TestResponseStucture(unittest.TestCase):
    base_url = 'http://localhost:8000/process'
    lang_codes = ('fi', 'en', 'et')
    audios = (os.path.join(os.getcwd(), 'test_samples/olen_kehittäjä.wav'),
              os.path.join(os.getcwd(), 'test_samples/i_am_developer.wav'),
              os.path.join(os.getcwd(), 'test_samples/olen_arendaja.wav'))

    texts = ('olen kehittäjä', 'i am developer', 'olen arendaja')
    aligns = [
        [{
            'start': 1.72,
            'end': 2.1,
            'features': {
                'aligned': 'olen'
            }
        }, {
            'start': 2.1,
            'end': 2.99,
            'features': {
                'aligned': 'kehittäjä'
            }
        }],
        [{
            'start': 0.0,
            'end': 0.01,
            'features': {
                'aligned': 'i'
            }
        }, {
            'start': 2.27,
            'end': 2.41,
            'features': {
                'aligned': 'am'
            }
        }, {
            'start': 2.42,
            'end': 2.69,
            'features': {
                'aligned': 'developer'
            }
        }],
        [{
            'start': 1.86,
            'end': 2.21,
            'features': {
                'aligned': 'olen'
            }
        }, {
            'start': 2.21,
            'end': 2.99,
            'features': {
                'aligned': 'arendaja'
            }
        }],
    ]

    data_aligns = dict(zip(lang_codes, aligns))

    def make_audio_req(self, lang, audio, text):
        """Prepare Audio Request based on
        lang code endpoint, audio, and text"""

        url = self.base_url + '/' + lang

        script = {"transcript": text}
        payload = {
            "type": "audio",
            "format": "LINEAR16",
            "sampleRate": 16000,
            "params": script
        }

        try:
            _ = os.path.isfile(audio)
            with open(audio, 'rb') as f:
                files = {
                    'request': (None, json.dumps(payload), 'application/json'),
                    'content':
                    (os.path.basename(audio), f.read(), 'audio/x-wav')
                }
        except Exception:
            files = {
                'request': (None, json.dumps(payload), 'application/json'),
                'content': (None, audio, 'audio/x-wav')
            }

        return url, files

    def test_api_response_status_code(self):
        """Should return status code 200 in 3 lang_codes endpoints
        """

        for lang, audio, text in zip(self.lang_codes, self.audios, self.texts):
            url, files = self.make_audio_req(lang, audio, text)
            status_code = requests.post(url, files=files).status_code
            self.assertEqual(status_code, 200)

        time.sleep(30)

    def test_api_response_status_code_with_wrong_end_point(self):
        """Should return ELG failure response in 3 wrong lang_codes endpoints
        """
        wrong_lang_codes = ['fini', 'engi', 'esti']
        for lang, audio, text in zip(wrong_lang_codes, self.audios,
                                     self.texts):
            url, files = self.make_audio_req(lang, audio, text)
            res = requests.post(url, files=files).json()
            self.assertIn('failure', res)
            self.assertEqual(res['failure']['errors'][0]['code'],
                             'elg.service.not.found')

        time.sleep(30)

    def test_api_response_result(self):
        """Should return ELG annotation response with correct aligned
        """

        for lang, audio, text in zip(self.lang_codes, self.audios, self.texts):
            url, files = self.make_audio_req(lang, audio, text)
            response = requests.post(url, files=files).json()
            print(response)

            self.assertEqual(response['response'].get('type'), 'annotations')
            for id, true_obj in enumerate(self.data_aligns[lang]):
                self.assertEqual(
                    response['response']['annotations']['forced_alignment'][id]
                    ['features'].get('aligned'),
                    true_obj['features']['aligned'])
                self.assertEqual(
                    response['response']['annotations']['forced_alignment']
                    [id].get('start'), true_obj['start'])
                self.assertEqual(
                    response['response']['annotations']['forced_alignment']
                    [id].get('end'), true_obj['end'])

        time.sleep(30)

    def test_api_response_too_small_audio_request(self):
        """Service should return ELG failure when
        too small audio file is sent
        """

        too_short_audio = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\
            \x01\x00\x00\x04\x00\x00\x00\x04\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00'

        for lang, text in zip(self.lang_codes, self.texts):
            url, files = self.make_audio_req(lang, too_short_audio, text)
            response = requests.post(url, files=files).json()
            print(response)
            self.assertIn('failure', response)
            self.assertEqual(
                response['failure']['errors'][0]['detail']['audio'],
                'File is empty or too small')
        time.sleep(30)

    def test_api_response_invalid_audio_format_request(self):
        """Service should return ELG failure when mp3 audio file is sent
        """

        mp3_audio = os.path.join(os.getcwd(),
                                 'test_samples/olen_kehittäjä.mp3')

        for lang, text in zip(self.lang_codes, self.texts):
            url, files = self.make_audio_req(lang, mp3_audio, text)
            response = requests.post(url, files=files).json()
            print(response)
            self.assertIn('failure', response)
            self.assertEqual(
                response['failure']['errors'][0]['detail']['audio'],
                'Audio is not in WAV format')
        time.sleep(30)


if __name__ == '__main__':
    unittest.main()
