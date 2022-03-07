import subprocess
import os
import shutil

main_dir = '/opt/kaldi/egs/align'  # this is the main directory of all calls
base_dir = f'{main_dir}/aligning_with_Docker/bin/'


def parse_ctm_to_json(ctm_file):
    with open(ctm_file, 'r') as f:
        aligns = [line.strip('\n').split(' ') for line in f]

    results = [{
        'start': float(start),
        'end': float(end),
        'features': {
            'aligned': text
        }
    } for start, end, text in aligns]
    return {"forced_alignment": results}


def predict(audio_name):
    expected_result_ctm = f'/opt/kaldi/egs/kohdistus/{audio_name[:-4]}.ctm'

    # These are 5 argunment for the pipeline in align.sh
    phone_csv_finn = 'phone-finnish-finnish.csv'
    debugBoolean = 'false'
    textDirTrue = 'textDirTrue'  # means there is transcript available
    src_for_wav = '/opt/kaldi/egs/kohdistus/src_for_wav'
    src_for_txt = '/opt/kaldi/egs/kohdistus/src_for_txt'

    subprocess.check_call([
        'sh', f'{base_dir}align.sh', phone_csv_finn, debugBoolean, textDirTrue,
        src_for_wav, src_for_txt
    ])

    try:
        os.path.exists(expected_result_ctm)
        return True, parse_ctm_to_json(expected_result_ctm)
    except FileNotFoundError:
        return False, 'Sorry, something wrong at our back-end when\
           processing the audio and script files'


def clean_up(src_for_wav, src_for_txt):
    data_dir = '/opt/kaldi/egs/kohdistus'
    shutil.rmtree(data_dir)
    # Recreate necessary dir since the aligner needs it always
    os.mkdir(data_dir)
    os.mkdir(src_for_wav)
    os.mkdir(src_for_txt)
