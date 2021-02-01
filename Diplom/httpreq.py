from __future__ import print_function
from googleapiclient.discovery import build, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
import json
from datetime import datetime
import os
import pickle
import os.path
import pathlib


class HttpRequester:
    _DEFAULT_BACKUP_DIR = 'AwesomePhotoBackups'
    _VK_TOKEN = 'resources/vk_token.txt'
    _YA_TOKEN = 'resources/ya_token.txt'
    _GOOGLE_TOKEN = 'resources/google_token.json'
    _INSTA_TOKEN = 'resources/insta_token.txt'
    _ODN_TOKEN = 'resources/odn_secret.txt'
    _LOG_DIR = 'logs/'
    _TMP_DIR = 'tmp/'

    def __init__(self, path, token_file, name):
        self.base_api_url = path
        self.name = name
        with open(token_file, 'r') as f:
            self.token = f.readline()

    def _join_url_path(self, *args):
        path = '/'.join(args)
        path = pathlib.PurePosixPath(path)
        path = path.parts
        path = f'{path[0]}//{"/".join(path[1:])}'
        return path


class YAHttpWorker(HttpRequester):
    __ENDPOINT_UPLOAD_URL = 'v1/disk/resources/upload'
    __ENDPOINT_GET_DIR = 'v1/disk/resources'

    def __init__(self):
        super(YAHttpWorker, self).__init__('https://cloud-api.yandex.net',
                                           self._YA_TOKEN,
                                           'Yandex'
                                           )
        self.token = 'OAuth ' + self.token

    def upload_url(self, url, file_name):
        status_code, get_upload_url_result = self.__get_upload_url(file_name)
        if status_code != 409:
            result = requests.post(self._join_url_path(self.base_api_url, self.__ENDPOINT_UPLOAD_URL),
                                   params={
                                       'path': file_name,
                                       'url': url,
                                   },
                                   headers={
                                       'Authorization': self.token
                                   }
                                   )
            result.raise_for_status()
        return status_code

    def __get_upload_url(self, path):
        result = requests.get(self._join_url_path(self.base_api_url, self.__ENDPOINT_UPLOAD_URL),
                              params={
                                  'path': path,
                              },
                              headers={
                                  'Authorization': self.token
                              }
                              )
        status_code = result.status_code
        if status_code == 409:
            return [status_code, '']
        result.raise_for_status()
        result = result.json()
        return [status_code, result['href']]

    def create_dir(self, folder=None):
        if folder is None:
            folder = self._DEFAULT_BACKUP_DIR
        else:

            folder = folder
        result = requests.put(self._join_url_path(self.base_api_url, self.__ENDPOINT_GET_DIR),
                              params={
                                  'path': folder,
                              },
                              headers={
                                  'Authorization': self.token
                              }
                              )
        if result.status_code != 409:
            result.raise_for_status()
        return folder

    def save_report(self, folder, data):
        file_name = f'Log_{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.txt'
        file_path = pathlib.PurePosixPath(folder, file_name).__str__()
        print(f'Saving Log File:\nLocaly: {file_name}\nRemotely: {file_path}')
        status_code, upload_url = self.__get_upload_url(file_path)
        if not os.path.exists(self._LOG_DIR):
            os.mkdir(self._LOG_DIR)
        with open(self._join_url_path(self._LOG_DIR, file_name), 'w') as f:
            f.write(json.dumps(data))
        with open(self._join_url_path(self._LOG_DIR, file_name), 'rb') as f:
            result = requests.put(upload_url,
                                  params={
                                      'path': file_path,
                                  },
                                  files={'file': f},
                                  headers={
                                      'Authorization': self.token
                                  }
                                  )
        result.raise_for_status()
        print('Done Saving Log File')


class GoogleHttpWorker(HttpRequester):
    __SCOPES = ['https://www.googleapis.com/auth/drive']

    __TYPE_FOLDER = 0
    __TYPE_FILE = 1

    def __init__(self):
        super(GoogleHttpWorker, self).__init__('https://www.googleapis.com',
                                               self._GOOGLE_TOKEN,
                                               'Google'
                                               )

        creds = None
        if os.path.exists('resources/google_token.pickle'):
            with open('resources/google_token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'resources/google_token.json', self.__SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('resources/google_token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

        if not os.path.exists(self._TMP_DIR):
            try:
                os.mkdir(self._TMP_DIR)
            except IOError:
                print('Warning: Could not create "tmp/" dir. This will lead to buffering Errors.'
                      'Please fix this before proceed.')

    def upload_file(self, file_url, name, parent_folder):
        file_existence = self.__check_existence(name, parent_folder, self.__TYPE_FILE)
        if len(file_existence) != 0:
            return 409

        result = requests.get(file_url)
        result.raise_for_status()
        with open(pathlib.PurePosixPath(self._TMP_DIR, name).__str__(), 'wb') as f:
            f.write(result.content)

        file = MediaFileUpload(
            pathlib.PurePosixPath(self._TMP_DIR, name).__str__(),
            mimetype='image/jpeg',
            resumable=True
        )

        file_metadata = {
            'name': f'{name}',
            'parents': [parent_folder],
        }

        _ = self.service.files().create(body=file_metadata,
                                        media_body=file,
                                        ).execute()
        return 200

    def __check_existence(self, name, root, search_type=None):
        if search_type == self.__TYPE_FOLDER or search_type is None:
            check_folder = self.service.files().list(
                q=f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{name}' and parents in '{root}'",
                fields="files(id, name, parents)"
            ).execute().get('files')
        elif search_type == self.__TYPE_FILE:
            check_folder = self.service.files().list(
                q=f"mimeType='image/jpeg' and trashed=false and name='{name}' and parents in '{root}'",
                fields="files(id, name, parents)"
            ).execute().get('files')
        else:
            return []
        return check_folder

    def create_dir(self, folder_name=None, root_folder=None):
        root_folder_id = self.service.files().get(fileId='root').execute().get('id')

        if folder_name is None or root_folder is None:
            folder = self._DEFAULT_BACKUP_DIR
        else:
            folder = folder_name
            root_folder_id = root_folder

        check_folder = self.__check_existence(folder, root_folder_id)

        file_metadata = {
            'name': f'{folder}',
            'parents': [root_folder_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if len(check_folder) == 0:
            folder = self.service.files().create(body=file_metadata,

                                                 ).execute()
            return folder.get('id')

        return check_folder[0]['id']

    def save_report(self, root_dir, data, saved_dir_name):
        file_name = f'Log_{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.txt'

        file_path = pathlib.PurePosixPath(self._DEFAULT_BACKUP_DIR, str(saved_dir_name), str(file_name)).__str__()
        print(f'Saving Log File:\nLocaly: {file_name}\nRemotely: {file_path}')
        if not os.path.exists(self._LOG_DIR):
            os.mkdir(self._LOG_DIR)
        with open(pathlib.PurePosixPath(self._LOG_DIR, file_name).__str__(), 'w') as f:
            f.write(json.dumps(data))

        file = MediaFileUpload(
            pathlib.PurePosixPath(self._LOG_DIR, file_name).__str__(),
            mimetype='text/plain',
            resumable=True
        )

        file_metadata = {
            'name': f'{file_name}',
            'parents': [root_dir],
        }

        _ = self.service.files().create(body=file_metadata,
                                        media_body=file,
                                        ).execute()
