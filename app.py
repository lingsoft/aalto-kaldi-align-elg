import utils

from elg import FlaskService
from elg.model import Failure, AudioRequest, AnnotationsResponse
from elg.model.base import StandardMessages

import os
import uuid  # for creatig random filename when needed

src_for_wav = '/opt/kaldi/egs/kohdistus/src_for_wav'
src_for_txt = '/opt/kaldi/egs/kohdistus/src_for_txt'

if not os.path.isdir(src_for_wav):
    os.makedirs(src_for_wav, exist_ok=True)

if not os.path.isdir(src_for_txt):
    os.makedirs(src_for_txt, exist_ok=True)


class AaltoAlign(FlaskService):
    def process_audio(self, request: AudioRequest):
        audio_file = request.content

        # checking audio filename
        try:
            audio_name = request.features[
                'fname']  # if meta data contains fname
        except KeyError:
            if request.format == 'LINEAR16':
                audio_name = str(uuid.uuid4()) + '.wav'
            else:
                detail = {
                    'request_invalid':
                    'Wrong input audio, check if audio format is wav'
                }
                error = StandardMessages.generate_elg_request_invalid(
                    detail=detail)
                return Failure(errors=[error])

        # checking transcript
        try:
            transcript = request.features['transcript']
        except KeyError:
            detail = {
                'request_invalid': 'No transcript text of audio file was given'
            }
            error = StandardMessages.generate_elg_request_missing(
                detail=detail)
            return Failure(errors=[error])

        # Ignoring too short transcript
        if len(transcript) < 3:
            detail = {
                'request_invalid':
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
            detail = {'server error': result}
            error = StandardMessages.generate_elg_service_internalerror(
                detail=detail)
            return Failure(errors=[error])


aalto_align = AaltoAlign("aalto_align-service")
app = aalto_align.app
