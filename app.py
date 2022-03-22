import utils

from elg import FlaskService
from elg.model import Failure, AudioRequest, AnnotationsResponse
from elg.model.base import StandardMessages

import io
import os
import sys
import uuid  # for creatig random filename when needed
import logging

from mutagen.wave import WAVE  # for audio info check

src_for_wav = '/opt/kaldi/egs/kohdistus/src_for_wav'
src_for_txt = '/opt/kaldi/egs/kohdistus/src_for_txt'

if not os.path.isdir(src_for_wav):
    os.makedirs(src_for_wav, exist_ok=True)

if not os.path.isdir(src_for_txt):
    os.makedirs(src_for_txt, exist_ok=True)


class AaltoAlign(FlaskService):
    def process_audio(self, request: AudioRequest):
        audio_file = request.content
        # validating file size
        try:
            audio_file_size = sys.getsizeof(audio_file) / (1024 * 1024)
        except ZeroDivisionError:
            err_msg = StandardMessages.generate_elg_request_invalid(
                detail={'audio': 'File is empty'})
            return Failure(errors=[err_msg])
        if audio_file_size > 25:  # maximum allow is 25MB
            err_msg = StandardMessages.generate_elg_upload_too_large(
                detail={'audio': 'File is over 25MB'})
            return Failure(errors=[err_msg])

        # validating file format
        try:
            audio_info = WAVE(io.BytesIO(audio_file)).info
        except TypeError:
            err_msg = StandardMessages.generate_elg_request_invalid(
                detail={'audio': 'Audio is not in WAV format'})
            return Failure(errors=[err_msg])

        logging.info('Sent audio info: ', audio_info.pprint())

        # checking audio filename
        try:
            audio_name = request.features['fname']
        except KeyError:
            audio_name = str(uuid.uuid4()) + '.wav'

        # checking transcript
        try:
            transcript = request.features['transcript']
        except KeyError:
            detail = {'transcript': 'No transcript was given'}
            error = StandardMessages.generate_elg_request_missing(
                detail=detail)
            return Failure(errors=[error])

        # too short transcript
        if len(transcript) < 3:
            detail = {
                'transcript':
                'Given transcript is too short, perhaps wrong transcript'
            }
            error = StandardMessages.generate_elg_request_invalid(
                detail=detail)
            return Failure(errors=[error])

        transcript_name = audio_name[:-4] + '.txt'

        audio_save_path = os.path.join(src_for_wav, audio_name)
        transcript_save_path = os.path.join(src_for_txt, transcript_name)

        # saving audio file
        with open(audio_save_path, 'wb') as fp:
            fp.write(audio_file)

        # saving transcript file
        with open(transcript_save_path, 'w') as fp:
            fp.write(transcript)

        # Call pipeline utilty
        is_success, result = utils.predict(audio_name)
        # Clean up all files
        utils.clean_up(src_for_wav, src_for_txt)
        if is_success:
            return AnnotationsResponse(annotations=result)
        else:
            error = StandardMessages.generate_elg_service_internalerror(
                params=[result])
            return Failure(errors=[error])


aalto_align = AaltoAlign("aalto_align-service")
app = aalto_align.app
