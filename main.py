import os
import stat
import shutil
import yaml
import time


from scripts.sub_download import (getUserToken, destroyUserToken, searchSubtitles,
                          getSubtitlesInfo, downloadSubtitles, getUserInfo)
from scripts.changetime import shift_subtitle
from scripts.easy_translate import translate_subtitles

def handle_remove_error(func, path, exc_info):
    print(f'Error removing {path}: {exc_info}')
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)


def make_writable_and_remove(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            os.chmod(file_path, stat.S_IWUSR)
        for name in dirs:
            dir_path = os.path.join(root, name)
            os.chmod(dir_path, stat.S_IWUSR)
    shutil.rmtree(path, onerror=handle_remove_error)


def download_sub(downloaded_en_dir, id_tv_show, season, from_eps, to_eps, username, password):
    for eps in range(from_eps, to_eps + 1):
        subtitlesResultList = searchSubtitles(parent_imdb_id=id_tv_show, order_by="download_count",
                                              order_direction="desc", languages='en', season_number=season,
                                              episode_number=eps)
        sub_id = subtitlesResultList['data'][0]['attributes']['files'][0]['file_id']
        user_token = getUserToken(username=username, password=password)
        sub_link = getSubtitlesInfo(user_token, sub_id)['link']

        download_sub_path = os.path.join(downloaded_en_dir, f"episode_{eps}")
        os.makedirs(download_sub_path, exist_ok=True)
        downloadSubtitles(user_token, sub_link, os.path.join(download_sub_path, f'episode_{eps}.srt'))

        user_info = getUserInfo(user_token)['data']
        print(f'Remaining Downloads : {user_info["remaining_downloads"]}')
        print(f'Remaining Reset Download Time : {user_info["reset_time"]}')
        destroyUserToken(user_token)
    print(f'Done!! Check Your file in {downloaded_en_dir}')


def sync_sub(downloaded_en_dir, change_time_dir, from_eps, to_eps, time_change, input_path_time):
    for eps in range(from_eps, to_eps + 1):
        sync_subtitle_path = os.path.join(change_time_dir, f"episode_{eps}")
        os.makedirs(sync_subtitle_path, exist_ok=True)

        download_sub_path = os.path.join(downloaded_en_dir, f"episode_{eps}")
        translate_dir_path = os.path.join(change_time_dir, f'episode_{eps}')

        if input_path_time == 1:
            shift_subtitle(os.path.join(download_sub_path, f'episode_{eps}.srt'),
                           os.path.join(sync_subtitle_path, f'episode_{eps}.srt'), milliseconds=time_change)
        else:
            shift_subtitle(os.path.join(translate_dir_path, f'episode_{eps}.srt'),
                           os.path.join(sync_subtitle_path, f'episode_{eps}.srt'), milliseconds=time_change)
    print(f'Done!! Check Your file in {change_time_dir}')


def translate(downloaded_en_dir, change_time_dir, translated_dir, from_eps, to_eps, target_language, input_path_trans):
    for eps in range(from_eps, to_eps + 1):
        translate_dir_path = os.path.join(translated_dir, f"episode_{eps}")
        if not os.path.isdir(translate_dir_path):
            os.makedirs(translate_dir_path, exist_ok=True)

        download_sub_path = os.path.join(downloaded_en_dir, f"episode_{eps}")
        sync_subtitle_path = os.path.join(change_time_dir, f"episode_{eps}")

        if input_path_trans == 1:
            translate_subtitles(os.path.join(download_sub_path, f"episode_{eps}.srt"),
                                os.path.join(translate_dir_path, f"episode_{eps}.srt"), target_language=target_language)
            time.sleep(3)
        else:
            translate_subtitles(os.path.join(sync_subtitle_path, f"episode_{eps}.srt"),
                                os.path.join(translate_dir_path, f"episode_{eps}.srt"), target_language=target_language)
            time.sleep(3)


if __name__ == "__main__":
    with open("config.yaml") as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    mode = conf["MODE"]
    season = conf['SEASON']
    from_eps = conf['FROM_EPISODE']
    to_eps = conf['TO_EPISODE']
    id_tv_show = conf['IMDB_ID_TV_SHOW']
    password = conf['PASSWORD']
    username = conf['USERNAME']
    time_change = conf['CHANGE_TIME']['MILLISECOND']
    input_path_time = conf['CHANGE_TIME']['INPUT_PATH']
    target_language = conf['TRANSLATE']['TARGET_LANGUAGE']
    input_path_trans = conf['TRANSLATE']['INPUT_PATH']

    translated_dir = os.path.join(os.getcwd(), 'data_subtitles', 'translated_subtitle')
    downloaded_en_dir = os.path.join(os.getcwd(), 'data_subtitles', 'downloaded_subtitle_en')
    sync_subtitle = os.path.join(os.getcwd(), 'data_subtitles', 'sync_subtitle')

    if mode == 1:
        make_writable_and_remove(downloaded_en_dir)
        download_sub(downloaded_en_dir, id_tv_show, season, from_eps, to_eps, username, password)

    elif mode == 2:
        make_writable_and_remove(sync_subtitle)
        sync_sub(downloaded_en_dir, sync_subtitle, from_eps, to_eps, time_change, input_path_time)

    else:
        make_writable_and_remove(translated_dir)
        translate(downloaded_en_dir, sync_subtitle, translated_dir, from_eps, to_eps, target_language,
                  input_path_trans)
