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


class ResourcesFactory:
    VK_TOKEN = 'resources/vk_token.txt'
    YA_TOKEN = 'resources/ya_token.txt'
    GOOGLE_TOKEN = 'resources/google_token.json'
    INSTA_TOKEN = 'resources/insta_token.txt'
    ODN_TOKEN = 'resources/odn_secret.txt'
    LOG_DIR = 'logs/'
    TMP_DIR = 'tmp/'


class HttpRequester:
    default_backup_dir = 'AwesomePhotoBackups'

    def __init__(self, path, token_file, name):
        self.base_api_url = path
        self.name = name
        with open(token_file, 'r') as f:
            self.token = f.readline()

    def join_url_path(self, *args):
        path = '/'.join(args)
        path = pathlib.PurePosixPath(path)
        path = path.parts
        path = f'{path[0]}//{"/".join(path[1:])}'
        return path

    def join_file_path(self, *args):
        return pathlib.PurePosixPath(*args).__str__()

    def get_status(self):
        if self.token != '':
            print(f'\t{self.name} Token load Success')
            return True
        else:
            return False

    def _generate_unique_names(self, data):
        for k, v in data.items():
            names_list = []
            for item in v:
                if item['name'] in names_list:
                    i = 1
                    while item['name'] in names_list:
                        item['name'] = '(' + str(i) + ')' + item['name']
                    names_list.append(item['name'])
                else:
                    names_list.append(item['name'])
        return data


class YAHttpWorker(HttpRequester):
    ENDPOINT_UPLOAD_URL = 'v1/disk/resources/upload'
    ENDPOINT_GET_DIR = 'v1/disk/resources'

    def __init__(self):
        super(YAHttpWorker, self).__init__('https://cloud-api.yandex.net',
                                           ResourcesFactory.YA_TOKEN,
                                           'Yandex'
                                           )
        self.token = 'OAuth ' + self.token

    def upload_url(self, url, file_name):
        status_code, get_upload_url_result = self.__get_upload_url(file_name)
        if status_code != 409:
            self.__upload_file(url, file_name)
        return status_code

    def __get_upload_url(self, path):
        result = requests.get(self.join_url_path(self.base_api_url, self.ENDPOINT_UPLOAD_URL),
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

    def __upload_file(self, external_resource_url, path):
        result = requests.post(self.join_url_path(self.base_api_url, self.ENDPOINT_UPLOAD_URL),
                               params={
                                   'path': path,
                                   'url': external_resource_url,
                               },
                               headers={
                                   'Authorization': self.token
                               }
                               )
        result.raise_for_status()

    def create_dir(self, folder=None):
        if folder is None:
            folder = self.default_backup_dir
        else:

            folder = folder
        result = requests.put(self.join_url_path(self.base_api_url, self.ENDPOINT_GET_DIR),
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
        #file_path = self.join_url_path(folder, file_name)
        file_path = pathlib.PureWindowsPath(folder, file_name).__str__()
        print(f'Saving Log File:\nLocaly: {file_name}\nRemotely: {file_path}')
        status_code, upload_url = self.__get_upload_url(file_path)
        if not os.path.exists(ResourcesFactory.LOG_DIR):
            os.mkdir(ResourcesFactory.LOG_DIR)
        with open(self.join_url_path(ResourcesFactory.LOG_DIR, file_name), 'w') as f:
            f.write(json.dumps(data))
        with open(self.join_url_path(ResourcesFactory.LOG_DIR, file_name), 'rb') as f:
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
    SCOPES = ['https://www.googleapis.com/auth/drive']

    TYPE_FOLDER = 0
    TYPE_FILE = 1

    def __init__(self):
        super(GoogleHttpWorker, self).__init__('https://www.googleapis.com',
                                               ResourcesFactory.GOOGLE_TOKEN,
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
                    'resources/google_token.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('resources/google_token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

        if not os.path.exists(ResourcesFactory.TMP_DIR):
            try:
                os.mkdir(ResourcesFactory.TMP_DIR)
            except IOError:
                print('Warning: Could not create "tmp/" dir. This will lead to buffering Errors.'
                      'Please fix this before proceed.')

    def upload_file(self, file_url, name, parent_folder):
        file_existence = self.__check_existence(name, parent_folder, self.TYPE_FILE)
        if len(file_existence) != 0:
            return 409

        result = requests.get(file_url)
        result.raise_for_status()
        with open(self.join_file_path(ResourcesFactory.TMP_DIR, name), 'wb') as f:
            f.write(result.content)

        file = MediaFileUpload(
            self.join_file_path(ResourcesFactory.TMP_DIR, name),
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
        if search_type == self.TYPE_FOLDER or search_type is None:
            check_folder = self.service.files().list(
                q=f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{name}' and parents in '{root}'",
                fields="files(id, name, parents)"
            ).execute().get('files')
        elif search_type == self.TYPE_FILE:
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
            folder = self.default_backup_dir
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
        file_path = self.join_file_path(self.default_backup_dir, str(saved_dir_name), str(file_name))
        print(f'Saving Log File:\nLocaly: {file_name}\nRemotely: {file_path}')
        if not os.path.exists(ResourcesFactory.LOG_DIR):
            os.mkdir(ResourcesFactory.LOG_DIR)
        with open(self.join_file_path(ResourcesFactory.LOG_DIR, file_name), 'w') as f:
            f.write(json.dumps(data))

        file = MediaFileUpload(
            self.join_file_path(ResourcesFactory.LOG_DIR, file_name),
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
