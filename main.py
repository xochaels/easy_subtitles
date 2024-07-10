import os
import sys
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


def selection_folder():
    while True:
        path_input_parent = int(input("""
        Choose Your Directory File That Your File Exists (1 or 2 or 3 or 4):
        1. Downloaded_subtitle_en
        2. Sync_subtitle
        3. Translated_subtitle
        4. Exit
        Your Answer (Choose one):
        """))

        if path_input_parent == 1:
            return downloaded_en_dir
        elif path_input_parent == 2:
            return sync_subtitle
        elif path_input_parent == 3:
            return translated_dir
        elif path_input_parent == 4:
            print("Exiting the program.")
            sys.exit()
        else:
            print("Invalid selection, please try again.")


def selection_file(parent_path):
    while True:
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
        0: Go back to folder selection
        999: Exit
        Your Answer (Choose one):
        """))

        if file_selection == 0:
            return None
        if file_selection == 999:
            sys.exit()
        elif 1 <= file_selection <= len(list_file['Directory Name']):
            file_answer = list_file['Directory Name'][file_selection - 1]
            print(f"You selected: {file_answer}")
            return file_answer
        else:
            print("Invalid file selection, please try again.")


def sync_sub(from_eps, to_eps, time_change):
    def sync_sub_and_save(input_path, path_target, file_name, time_change):
        if os.path.exists(path_target):
            make_writable_and_remove(path_target)
        os.makedirs(path_target, exist_ok=True)

        sub_name = os.path.join(path_target, f'{file_name}')
        shift_subtitle(input_path, sub_name, milliseconds=time_change)
        print(f'Done! Check your file in {sub_name}')

    while True:
        parent_path = selection_folder()
        while True:
            file_answer = selection_file(parent_path)
            if file_answer is None:
                break

            if type_mode == 1:
                input_path = os.path.join(parent_path, file_answer, f"{file_answer}.srt")
                target_path = os.path.join(sync_subtitle, file_answer)
                sync_sub_and_save(input_path, target_path, f"{file_answer}.srt", time_change)
            else:
                for eps in range(from_eps, to_eps + 1):
                    input_path = os.path.join(parent_path, file_answer, f"episode_{eps}", f"episode_{eps}.srt")
                    target_path = os.path.join(sync_subtitle, file_answer, f"episode_{eps}")
                    sync_sub_and_save(input_path, target_path, f"episode_{eps}.srt", time_change)


def translate(from_eps, to_eps, target_language):
    def translate_sub_and_save(input_path, target_path, file_name, target_language):
        if os.path.exists(target_path):
            make_writable_and_remove(target_path)
        os.makedirs(target_path, exist_ok=True)

        sub_name = os.path.join(target_path, f'{file_name}')
        translate_subtitles(input_path, sub_name, target_language=target_language)
        print(f'Done! Check your file in {sub_name}')
        time.sleep(1)

    while True:
        parent_path = selection_folder()
        while True:
            file_answer = selection_file(parent_path)
            if file_answer is None:
                break

            if type_mode == 1:
                input_path = os.path.join(parent_path, file_answer, f"{file_answer}.srt")
                target_path = os.path.join(translated_dir, file_answer)
                translate_sub_and_save(input_path, target_path, f"{file_answer}.srt", target_language=target_language)
            else:
                for eps in range(from_eps, to_eps + 1):
                    input_path = os.path.join(parent_path, file_answer, f"episode_{eps}", f"episode_{eps}.srt")
                    target_path = os.path.join(translated_dir, file_answer, f"episode_{eps}")
                    translate_sub_and_save(input_path, target_path, f"episode_{eps}.srt", target_language=target_language)


def llm_translate(from_eps, to_eps, target_language):
    def llm_translate_sub_and_save(input_path, target_path, file_name, target_language):
        if os.path.exists(target_path):
            make_writable_and_remove(target_path)
        os.makedirs(target_path, exist_ok=True)

        sub_name = os.path.join(target_path, f'{file_name}')
        get_llm_translate(input_path, sub_name, target_language=target_language, model=model_llm, url=url)
        print(f'Done! Check your file in {sub_name}')
        time.sleep(1)

    while True:
        parent_path = selection_folder()
        while True:
            file_answer = selection_file(parent_path)
            if file_answer is None:
                break

            if type_mode == 1:
                input_path = os.path.join(parent_path, file_answer, f"{file_answer}.srt")
                target_path = os.path.join(translated_dir, file_answer)
                llm_translate_sub_and_save(input_path, target_path,
                                           f"{file_answer}.srt", target_language=target_language)
            else:
                for eps in range(from_eps, to_eps + 1):
                    input_path = os.path.join(parent_path, file_answer, f"episode_{eps}", f"episode_{eps}.srt")
                    target_path = os.path.join(translated_dir, file_answer, f"episode_{eps}")
                    llm_translate_sub_and_save(input_path, target_path,
                                               f"episode_{eps}.srt", target_language=target_language)

# def film_type():
#     while True:
#         text = """
#             Please fill the config.yaml file before run this!
#             Choose Type :
#             1. Movies
#             2. TV Shows
#             3. Exit
#             """
#         print(text)
#         type_selection = int(input("Please select an option (Choose One) : "))
#         if type_selection == 1:
#             translated_dir = os.path.join(os.getcwd(), 'data_subtitles', 'movies', 'translated_subtitle')
#             downloaded_en_dir = os.path.join(os.getcwd(), 'data_subtitles', 'movies', 'downloaded_subtitle_en')
#             sync_subtitle = os.path.join(os.getcwd(), 'data_subtitles', 'movies', 'sync_subtitle')
#         elif type_selection == 2:
#             translated_dir = os.path.join(os.getcwd(), 'data_subtitles', 'tv_show', 'translated_subtitle')
#             downloaded_en_dir = os.path.join(os.getcwd(), 'data_subtitles', 'tv_show', 'downloaded_subtitle_en')
#             sync_subtitle = os.path.join(os.getcwd(), 'data_subtitles', 'tv_show', 'sync_subtitle')
#         elif type_selection == 4:
#             sys.exit()
#         else:
#             print("Invalid file selection, please try again.")
#
#
#
# def main_menu():
#     while True:
#         text = """
#
#         Menu:
#         1. Download Subtitle
#         2. Sync Subtitle
#         3. Translate Subtitle with Google Translate
#         4. Translate Subtitle with Offline LLM
#         5. Exit
#         """
#         print(text)
#         menu_selection = int(input("Please select an option (Choose One) : "))
#         if menu_selection == 1:
#             return download_sub(id_movie, id_tv_show, season, from_eps, to_eps, username, password)
#         elif menu_selection == 2:
#             return sync_sub(from_eps, to_eps, time_change)
#         elif menu_selection == 3:
#             return translate(from_eps, to_eps, target_language=target_language)
#         elif menu_selection == 4:
#             return llm_translate(from_eps, to_eps, target_language=target_language)
#         elif menu_selection == 5:
#             return sys.exit()
#         else:
#             print("Invalid file selection, please try again.")



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
    target_language = conf['TRANSLATE']['TARGET_LANGUAGE']
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
        translate(from_eps, to_eps, target_language=target_language)
    else:
        llm_translate(from_eps, to_eps, target_language=target_language)
