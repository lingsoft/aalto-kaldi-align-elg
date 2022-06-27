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
MIN_TRANSCRIPT = 3


class AaltoAlign(FlaskService):

    def process_audio(self, request: AudioRequest):
        lang = self.url_param('lang_code')
        if lang not in SUPPORT_LANGS:
            err_msg = StandardMessages.generate_elg_service_not_found(
                params=[lang])
            return Failure(errors=[err_msg])

        for elem in ["format", "content"]:
            if (not hasattr(request, elem)) or (getattr(request, elem) is None):
                mp_msg = "Missing property {}".format(elem)
                err_msg = StandardMessages.generate_elg_request_invalid(
                        detail={"request": mp_msg})
                return Failure(errors=[err_msg])

        transcript = (request.params or {}).get('transcript')
        if not transcript:
            # this is a standard message code but it has not yet been included in a
            # released version of StandardMessagesi (IR 2022-06-23)
            err_msg = StatusMessage(code="elg.request.parameter.missing",
                text="Required parameter {0} missing from request",
                params=["transcript"])
            return Failure(errors=[err_msg])

        if len(transcript) < MIN_TRANSCRIPT:
            # Do not use "elg." prefix for custom message codes (IR 2022-06-23)
            error = StatusMessage(code="lingsoft.transcript.too.short",
                text="Given transcript is too short")
            return Failure(errors=[error])
        if request.format != AUDIO_FORMAT:
            err_msg = StandardMessages.generate_elg_request_audio_format_unsupported(
                    params=[request.format])
            return Failure(errors=[err_msg])

        audio_file = request.content

        audio_file_size = sys.getsizeof(audio_file) / 1024
        if audio_file_size < MIN_FILE_SIZE:
            err_msg = StandardMessages.generate_elg_request_invalid(
                detail={'audio': 'File is empty or too small'})
            return Failure(errors=[err_msg])
        if audio_file_size > MAX_FILE_SIZE: 
            err_msg = StandardMessages.generate_elg_upload_too_large(
                detail={'audio': 'File is over 25MB'})
            return Failure(errors=[err_msg])

        try:
            audio_info = WAVE(io.BytesIO(audio_file)).info
        except Exception:
            err_msg = StandardMessages.generate_elg_request_audio_format_unsupported(
                    params=["different from WAV"])
            return Failure(errors=[err_msg])
        if audio_info.sample_rate != SAMPLE_RATE:
            err_msg = StandardMessages.generate_elg_request_audio_samplerate_unsupported(
                    params=[str(audio_info.sample_rate)])
            return Failure(errors=[err_msg])

        # In specs sampleRate but in ELG Python SDK sample_rate
        # https://european-language-grid.readthedocs.io/en/stable/all/A1_PythonSDK/Model.html#module-elg.model.request.AudioRequest
        sampleRate_warning_msg = None
        if request.sample_rate and (request.sample_rate != audio_info.sample_rate):
            sampleRate_warning_msg = StatusMessage(
                code='lingsoft.sampleRate.value.mismatch',
                params=[str(request.sample_rate), str(audio_info.sample_rate)],
                text=
                'Parameter sample rate {0} does not match file sample rate {1}'
            )

        audio_name = str(uuid.uuid4()) + '.wav'
        transcript_name = audio_name[:-4] + '.txt'
        audio_save_path = os.path.join(src_for_wav, audio_name)
        transcript_save_path = os.path.join(src_for_txt, transcript_name)

        with open(audio_save_path, 'wb') as fp:
            fp.write(audio_file)

        with open(transcript_save_path, 'w') as fp:
            fp.write(transcript)

        is_success, result = utils.predict(audio_name, lang)
        utils.clean_up(audio_name)

        if is_success:
            resp = AnnotationsResponse(annotations=result)
            if sampleRate_warning_msg:
                resp.warnings = [sampleRate_warning_msg]
            return resp
        else:
            error = StandardMessages.generate_elg_service_internalerror(
                params=[result])
            return Failure(errors=[error])


aalto_align = AaltoAlign(name="aalto_align-service",
                         path="/process/<lang_code>")
app = aalto_align.app
