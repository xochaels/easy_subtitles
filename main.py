import os
import stat
import shutil
import yaml
import time

from scripts.sub_download import (getUserToken, destroyUserToken, searchSubtitles,
                                  getSubtitlesInfo, downloadSubtitles, getUserInfo)
from scripts.changetime import shift_subtitle
from scripts.easy_translate import translate_subtitles
from scripts.llm_translate import get_llm_translate


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


def download_sub(id_movie, id_tv_show, season, from_eps, to_eps, username, password):
    def download_and_save_subtitle(sub_id, sub_title, sub_path, username, password):
        user_token = getUserToken(username=username, password=password)
        sub_link = getSubtitlesInfo(user_token, sub_id)['link']

        if os.path.exists(sub_path):
            make_writable_and_remove(sub_path)
        os.makedirs(sub_path, exist_ok=True)

        downloadSubtitles(user_token, sub_link, os.path.join(sub_path, f'{sub_title}.srt'))

        user_info = getUserInfo(user_token)['data']
        print(f'Remaining Downloads: {user_info["remaining_downloads"]}')
        print(f'Remaining Reset Download Time: {user_info["reset_time"]}')
        destroyUserToken(user_token)
        print(f'Done! Check your file in {sub_path}')

    if type_mode == 1:
        subtitlesResultList = searchSubtitles(imdb_id=id_movie, order_by="download_count",
                                              order_direction="desc", languages='en')
        sub_id = subtitlesResultList['data'][0]['attributes']['files'][0]['file_id']
        sub_title = subtitlesResultList['data'][0]['attributes']['feature_details']['title']
        download_sub_path = os.path.join(downloaded_en_dir, sub_title)
        download_and_save_subtitle(sub_id, sub_title, download_sub_path, username, password)

    else:
        for eps in range(from_eps, to_eps + 1):
            subtitlesResultList = searchSubtitles(parent_imdb_id=id_tv_show, order_by="download_count",
                                                  order_direction="desc", languages='en', season_number=season,
                                                  episode_number=eps)
            sub_id = subtitlesResultList['data'][0]['attributes']['files'][0]['file_id']
            sub_title = subtitlesResultList['data'][0]['attributes']['feature_details']['parent_title']
            episode_path = os.path.join(downloaded_en_dir, sub_title, f"episode_{eps}")
            download_and_save_subtitle(sub_id, f'episode_{eps}', episode_path, username, password)


def sync_sub(from_eps, to_eps, time_change):
    def sync_sub_and_save(input_path, path_target, file_name, time_change):
        if os.path.exists(path_target):
            make_writable_and_remove(path_target)
        os.makedirs(path_target, exist_ok=True)

        sub_name = os.path.join(path_target, f'{file_name}')
        shift_subtitle(input_path, sub_name, milliseconds=time_change)
        print(f'Done! Check your file in {sub_name}')

    path_input_parent = int(input("""
    Choose Your Directory File That Your File Exists (1 or 2 or 3):
    1. Downloaded_subtitle_en
    2. Sync_subtitle
    3. Translated_subtitle
    Your Answer (Choose one):
    """))

    if path_input_parent == 1:
        parent_path = downloaded_en_dir
    elif path_input_parent == 2:
        parent_path = sync_subtitle
    elif path_input_parent == 3:
        parent_path = translated_dir
    else:
        print("Invalid selection")
        return

    list_file = {
        'No': [],
        'Directory Name': []
    }
    for i, dirs in enumerate(os.listdir(parent_path), start=1):
        list_file['No'].append(i)
        list_file['Directory Name'].append(dirs)

    display_list = '\n'.join([f"{no}: {name}" for no, name in zip(list_file['No'], list_file['Directory Name'])])
    file_selection = int(input(f"""
    Choose Your File That You Want to Change:
    {display_list}
    Your Answer (Choose one):
    """))

    if file_selection < 1 or file_selection > len(list_file['Directory Name']):
        print("Invalid file selection")
        return

    file_answer = list_file['Directory Name'][file_selection - 1]
    print(f"You selected: {file_answer}")

    if type_mode == 1:
        input_path = os.path.join(parent_path, file_answer, f"{file_answer}.srt")
        target_path = os.path.join(sync_subtitle, file_answer)
        sync_sub_and_save(input_path, target_path, f"{file_answer}.srt", time_change)
    else:
        for eps in range(from_eps, to_eps + 1):
            input_path = os.path.join(parent_path, file_answer, f"episode_{eps}", f"episode_{eps}.srt")
            target_path = os.path.join(sync_subtitle, file_answer, f"episode_{eps}")
            sync_sub_and_save(input_path, target_path, f"episode_{eps}.srt", time_change)

def translate(downloaded_en_dir, sync_subtitle, translated_dir, from_eps, to_eps, target_language, input_path_trans):
    for eps in range(from_eps, to_eps + 1):
        translate_dir_path = os.path.join(translated_dir, f"episode_{eps}")
        if not os.path.isdir(translate_dir_path):
            os.makedirs(translate_dir_path, exist_ok=True)

        download_sub_path = os.path.join(downloaded_en_dir, f"episode_{eps}")
        sync_subtitle_path = os.path.join(sync_subtitle, f"episode_{eps}")

        if input_path_trans == 1:
            translate_subtitles(os.path.join(download_sub_path, f"episode_{eps}.srt"),
                                os.path.join(translate_dir_path, f"episode_{eps}.srt"), target_language=target_language)
            time.sleep(1)
        else:
            translate_subtitles(os.path.join(sync_subtitle_path, f"episode_{eps}.srt"),
                                os.path.join(translate_dir_path, f"episode_{eps}.srt"), target_language=target_language)
            time.sleep(1)


def llm_translate(downloaded_en_dir, sync_subtitle, translated_dir, from_eps, to_eps, target_language, model_llm, url,
                  input_path_trans, num_workers=10):
    for eps in range(from_eps, to_eps + 1):
        translate_dir_path = os.path.join(translated_dir, f"episode_{eps}")
        if not os.path.isdir(translate_dir_path):
            os.makedirs(translate_dir_path, exist_ok=True)

        download_sub_path = os.path.join(downloaded_en_dir, f"episode_{eps}")
        sync_subtitle_path = os.path.join(sync_subtitle, f"episode_{eps}")

        if input_path_trans == 1:
            get_llm_translate(subtitle_path=os.path.join(download_sub_path, f"episode_{eps}.srt"),
                              target_path=os.path.join(translate_dir_path, f"episode_{eps}.srt"),
                              target_language=target_language,model=model_llm, url=url, num_workers=num_workers)
        else:
            get_llm_translate(subtitle_path=os.path.join(sync_subtitle_path, f"episode_{eps}.srt"),
                              target_path=os.path.join(translate_dir_path, f"episode_{eps}.srt"),
                              target_language=target_language,model=model_llm, url=url, num_workers=num_workers)


if __name__ == "__main__":
    with open("config.yaml") as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    mode = conf["MODE"]
    type_mode = conf['TYPE']
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
    model_llm = conf['TRANSLATE']['LLM_MODEL']
    url = conf['TRANSLATE']['LLM_URL']
    id_movie = conf['IMDB_ID_MOVIES']

    if type_mode == 1:
        translated_dir = os.path.join(os.getcwd(), 'data_subtitles', 'movies', 'translated_subtitle')
        downloaded_en_dir = os.path.join(os.getcwd(), 'data_subtitles', 'movies', 'downloaded_subtitle_en')
        sync_subtitle = os.path.join(os.getcwd(), 'data_subtitles', 'movies', 'sync_subtitle')
    else:
        translated_dir = os.path.join(os.getcwd(), 'data_subtitles', 'tv_show', 'translated_subtitle')
        downloaded_en_dir = os.path.join(os.getcwd(), 'data_subtitles', 'tv_show', 'downloaded_subtitle_en')
        sync_subtitle = os.path.join(os.getcwd(), 'data_subtitles', 'tv_show', 'sync_subtitle')

    if mode == 1:
        download_sub(id_movie, id_tv_show, season, from_eps, to_eps, username, password)

    elif mode == 2:
        sync_sub(from_eps, to_eps, time_change)

    elif mode == 3:
        make_writable_and_remove(translated_dir)
        translate(downloaded_en_dir, sync_subtitle, translated_dir, from_eps, to_eps, target_language,
                  input_path_trans)
    else:
        llm_translate(downloaded_en_dir, sync_subtitle, translated_dir, from_eps, to_eps, target_language, model_llm,
                      url,input_path_trans, num_workers=10)

