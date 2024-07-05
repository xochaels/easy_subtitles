import json
import urllib
import urllib.error
import urllib.parse
import urllib.request


API_URL = 'https://api.opensubtitles.com/api/v1/'
API_URL_LOGIN = API_URL + 'login'
API_URL_LOGOUT = API_URL + 'logout'
API_URL_SEARCH = API_URL + 'subtitles'
API_URL_DOWNLOAD = API_URL + 'download'
API_URL_USER_INFO = API_URL + 'infos/user'


APP_NAME = 'OpenSubtitlesDownload'
APP_VERSION = '6.3'
APP_API_KEY = 'FNyoC96mlztsk3ALgNdhfSNapfFY9lOi'


def getUserToken(username, password):
    try:
        headers = {
            "User-Agent": f"{APP_NAME} v{APP_VERSION}",
            "Api-key": f"{APP_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "username": username,
            "password": password
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(API_URL_LOGIN, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

        return response_data['token']

    except (urllib.error.HTTPError, urllib.error.URLError) as err:
        print("Urllib error (", err.code, ") ", err.reason)


def destroyUserToken(USER_TOKEN):
    try:
        headers = {
            "User-Agent": f"{APP_NAME} v{APP_VERSION}",
            "Api-key": f"{APP_API_KEY}",
            "Authorization": f"Bearer {USER_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(API_URL_LOGOUT, headers=headers, method='DELETE')
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

        return response_data

    except (urllib.error.HTTPError, urllib.error.URLError) as err:
        print("Urllib error (", err.code, ") ", err.reason)

def searchSubtitles(**kwargs):
    try:
        headers = {
            "User-Agent": f"{APP_NAME} v{APP_VERSION}",
            "Api-key": f"{APP_API_KEY}"
        }

        query_params = urllib.parse.urlencode(kwargs)
        url = f"{API_URL_SEARCH}?{query_params}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

        return response_data

    except (urllib.error.HTTPError, urllib.error.URLError) as err:
        print("Urllib error (", err.code, ") ", err.reason)


def getSubtitlesInfo(USER_TOKEN, file_id):
    try:
        headers = {
            "User-Agent": f"{APP_NAME} v{APP_VERSION}",
            "Api-key": f"{APP_API_KEY}",
            "Authorization": f"Bearer {USER_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "file_id": file_id
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(API_URL_DOWNLOAD, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

        return response_data

    except (urllib.error.HTTPError, urllib.error.URLError) as err:
        print("Urllib error (", err.code, ") ", err.reason)


def downloadSubtitles(USER_TOKEN, subURL, subPath):
    try:
        headers = {
            "User-Agent": f"{APP_NAME} v{APP_VERSION}",
            "Api-key": f"{APP_API_KEY}",
            "Authorization": f"Bearer {USER_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(subURL, headers=headers)
        with urllib.request.urlopen(req) as response:
            decodedStr = response.read().decode('utf-8')
            byteswritten = open(subPath, 'w', encoding='utf-8', errors='replace').write(decodedStr)
            if byteswritten > 0:
                return 0

        return 1

    except (urllib.error.HTTPError, urllib.error.URLError) as err:
        print("Urllib error (", err.code, ") ", err.reason)


def getUserInfo(USER_TOKEN):
    try:
        headers = {
            "User-Agent": f"{APP_NAME} v{APP_VERSION}",
            "Authorization": f"Bearer {USER_TOKEN}",
            "Accept": "application/json",
             "Api-key": f"{APP_API_KEY}",
        }

        req = urllib.request.Request(API_URL_USER_INFO, headers=headers)
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

        return response_data

    except (urllib.error.HTTPError, urllib.error.URLError) as err:
        print("Urllib error (", err.code, ") ", err.reason)
