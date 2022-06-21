import utils

from elg import FlaskService
from elg.model import Failure, AudioRequest, AnnotationsResponse
from elg.model.base import StandardMessages
from elg.model.base import StatusMessage

import io
import os
import sys
import uuid  # for creatig random filename when needed

from mutagen.wave import WAVE  # for audio info check

src_for_wav = '/opt/kaldi/egs/kohdistus/src_for_wav'
src_for_txt = '/opt/kaldi/egs/kohdistus/src_for_txt'

if not os.path.isdir(src_for_wav):
    os.makedirs(src_for_wav, exist_ok=True)

if not os.path.isdir(src_for_txt):
    os.makedirs(src_for_txt, exist_ok=True)

SUPPORT_LANGS = ('fi', 'en', 'se', 'et', 'kv')
AUDIO_FORMAT = "LINEAR16"
SAMPLE_RATE = 16000
MIN_FILE_SIZE = 20
MAX_FILE_SIZE = 25600

class AaltoAlign(FlaskService):

    def process_audio(self, request: AudioRequest):
        lang = self.url_param('lang_code')
        if lang not in SUPPORT_LANGS:
            err_msg = StandardMessages.generate_elg_service_not_found(
                params=[lang])
            return Failure(errors=[err_msg])

        audio_file = request.content

        if request.format != AUDIO_FORMAT:
            err_msg = StandardMessages.generate_elg_request_audio_format_unsupported(
                    params=[request.format])
            return Failure(errors=[err_msg])

        # validating file size
        audio_file_size = sys.getsizeof(audio_file) / 1024
        if audio_file_size < MIN_FILE_SIZE:
            err_msg = StandardMessages.generate_elg_request_invalid(
                detail={'audio': 'File is empty or too small'})
            return Failure(errors=[err_msg])
        if audio_file_size > MAX_FILE_SIZE: 
            err_msg = StandardMessages.generate_elg_upload_too_large(
                detail={'audio': 'File is over 25MB'})
            return Failure(errors=[err_msg])

        # validating file format and sample rate
        try:
            audio_info = WAVE(io.BytesIO(audio_file)).info
        except Exception:
            err_msg = StandardMessages.generate_elg_request_audio_format_unsupported(
                    params=["different from WAV"])
            return Failure(errors=[err_msg])
        if hasattr(request, 'sample_rate') and request.sample_rate != SAMPLE_RATE:
            err_msg = StandardMessages.generate_elg_request_audio_samplerate_unsupported(
                    params=[request.sample_rate])
            return Failure(errors=[err_msg])
        if audio_info.sample_rate != SAMPLE_RATE:
            err_msg = StandardMessages.generate_elg_request_audio_samplerate_unsupported(
                    params=[audio_info.sample_rate])
            return Failure(errors=[err_msg])
        
        # checking transcript
        try:
            transcript = request.params['transcript']
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

        audio_name = str(uuid.uuid4()) + '.wav'
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
        is_success, result = utils.predict(audio_name, lang)

        # Clean up all files
        utils.clean_up(audio_name)

        if is_success:
            return AnnotationsResponse(annotations=result)
        else:
            error = StandardMessages.generate_elg_service_internalerror(
                params=[result])
            return Failure(errors=[error])


aalto_align = AaltoAlign(name="aalto_align-service",
                         path="/process/<lang_code>")
app = aalto_align.app
