import subprocess
import os
import glob

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


def get_phone_csv(lang):
    if lang == 'en':
        csv_file = "phone-english-finnish.csv"
    elif lang == 'se':
        csv_file = "phone-sami-finnish.csv"
    elif lang == 'et':
        csv_file = "phone-estonian-finnish.csv"
    elif lang == 'kv':
        csv_file = "phone-komi-finnish.csv"
    else:
        csv_file = "phone-finnish-finnish.csv"
    return csv_file


def predict(audio_name, lang='fi'):
    expected_result_ctm = f'/opt/kaldi/egs/kohdistus/{audio_name[:-4]}.ctm'

    # These are 5 argunment for the pipeline in align.sh
    phone_csv_file = get_phone_csv(lang)
    debugBoolean = 'false'
    textDirTrue = 'textDirTrue'  # means there is transcript available
    src_for_wav = '/opt/kaldi/egs/kohdistus/src_for_wav'
    src_for_txt = '/opt/kaldi/egs/kohdistus/src_for_txt'

    subprocess.check_call([
        'sh', f'{base_dir}align.sh', phone_csv_file, debugBoolean, textDirTrue,
        src_for_wav, src_for_txt
    ])

    try:
        os.path.exists(expected_result_ctm)
        return True, parse_ctm_to_json(expected_result_ctm)
    except FileNotFoundError:
        return False, 'Something went wrong at back-end'


def clean_up(audio_name):
    audio_src_data_lst = glob.glob(
        f'/opt/kaldi/egs/kohdistus/*/{audio_name[:-4]}*')

    result_file_lst = glob.glob(f'/opt/kaldi/egs/kohdistus/{audio_name[:-4]}*')

    for filePath in audio_src_data_lst:
        try:
            os.remove(filePath)
        except FileNotFoundError:
            print('Error while removing file: ', filePath)

    for filePath in result_file_lst:
        try:
            os.remove(filePath)
        except FileNotFoundError:
            print('Error while removing file: ', filePath)
