from __future__ import print_function
from googleapiclient.discovery import build, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
from enum import Enum
import json
from datetime import datetime
import os
import pickle
import os.path


class _ResourcesFactory(Enum):
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
        if isinstance(token_file, _ResourcesFactory):
            with open(token_file.value, 'r') as f:
                self.token = f.readline()
        else:
            raise Exception('Token should be type of _ResourcesFactory')

    def join_url_path(self, *args):
        return '/'.join(args)

    def get_albums(self, user_id, count):
        pass

    def get_photos_list(self):
        pass

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


class VKHttpWorker(HttpRequester):
    __api_version = '5.126'

    class Photos(Enum):
        GET = 'photos.get'

    class Users(Enum):
        GET = 'users.get'

    class Albums(Enum):
        GET = 'photos.getAlbums'

    def __init__(self):
        super(VKHttpWorker, self).__init__('https://api.vk.com/method',
                                           _ResourcesFactory.VK_TOKEN,
                                           'VK'
                                           )

    def get_albums(self, user_id, count=None):
        albums = {}
        if not str(user_id).isdigit():
            user_id = self.__get_user_id(user_id)
        if user_id is not None:
            photos_count, photos_list = self.__get_photos(user_id)
            if photos_count == 0:
                return [0, {}]
            if count is not None:
                photos_list.sort(key=lambda x: x['sizes'][-1]['width'] * x['sizes'][-1]['height'])
                photos_list = photos_list[:count]
                photos_count = count
            for photo in photos_list:
                if albums.get(photo['album_id']) is None:
                    albums[photo['album_id']] = []
                albums[photo['album_id']].append({
                    'name': str(photo['likes']['count']) + '.jpg',
                    'url': photo['sizes'][-1]['url'],
                    'width': photo['sizes'][-1]['width'],
                    'height': photo['sizes'][-1]['height'],
                    'size': photo['sizes'][-1]['type']
                })
            albums = self._generate_unique_names(albums)
            return [photos_count, albums]
        else:
            return [0, {}]

    def __get_photos(self, user_id):
        result = requests.get(self.join_url_path(self.base_api_url, self.Photos.GET.value),
                              params={
                                  'owner_id': user_id,
                                  'access_token': self.token,
                                  'v': self.__api_version,
                                  'album_id': 'profile',
                                  'extended': 1
                              })
        result.raise_for_status()
        if result.json().get('error') is None:
            return [len(result.json()['response']['items']), result.json()['response']['items']]
        else:
            return [0, {}]

    def __get_user_id(self, user_id):
        result = requests.get(self.join_url_path(self.base_api_url, self.Users.GET.value),
                              params={
                                  'user_ids': user_id,
                                  'v': self.__api_version,
                                  'access_token': self.token
                              })
        result.raise_for_status()
        result = result.json()
        if result.get('error') is None:
            if len(result['response']) > 1:
                return None
            else:
                return result['response'][0]['id']
        else:
            return None


class ODNHttpWorker(HttpRequester):
    class PHOTO(Enum):
        GET = 'fb.do?method=friends.get'

    class AUTH(Enum):
        GET = 'https://connect.ok.ru/oauth/authorize'

    def __init__(self):
        super(ODNHttpWorker, self).__init__('https://api.ok.ru',
                                            _ResourcesFactory.ODN_TOKEN,
                                            'Odnoklassniki')

    def get_albums(self, user_id, count):
        return [0, 0]


class InstaHttpWorker(HttpRequester):
    class MEDIA(Enum):
        GET = 'media'

    def __init__(self):
        super(InstaHttpWorker, self).__init__('https://graph.instagram.com',
                                              _ResourcesFactory.INSTA_TOKEN,
                                              'Instagram')

    def get_albums(self, user_id, count=None):
        if not user_id.isdigit():
            return [0, 0]
        else:

            result = requests.get(self.join_url_path(self.base_api_url, user_id, self.MEDIA.GET.value),
                                  params={
                                      'access_token': self.token
                                  })
            result.raise_for_status()

            media_ids = result.json()['data']
            media_ids = media_ids[:count]

            albums = {'NO_ALBUM': []}
            counter = 0
            for media in media_ids:
                result = requests.get(self.join_url_path(self.base_api_url, media['id']),
                                      params={
                                          'access_token': self.token,
                                          'fields': 'media_url,media_type,children'
                                      })
                result.raise_for_status()
                result = result.json()

                if result['media_type'] == 'IMAGE':
                    albums['NO_ALBUM'].append({
                        'name': result['id'] + '.jpg',
                        'url': result['media_url'],
                        'width': None,
                        'height': None,
                        'size': '-'
                    })
                    counter += 1
                elif result['media_type'] == 'CAROUSEL_ALBUM':
                    albums[result['id']] = []
                    for children in result['children']:
                        sub_result = requests.get(self.join_url_path(self.base_api_url, children['id']),
                                                  params={
                                                      'access_token': self.token,
                                                      'fields': 'media_url,media_type'
                                                  })
                        sub_result.raise_for_status()
                        sub_result = sub_result.json()
                        if result['media_type'] == 'IMAGE':
                            albums[result['id']].append({
                                'name': sub_result['id'] + '.jpg',
                                'url': sub_result['media_url'],
                                'width': None,
                                'height': None,
                                'size': '-'
                            })
                        counter += 1
        albums = self._generate_unique_names(albums)
        return [counter, albums]


class YAHttpWorker(HttpRequester):
    class Upload(Enum):
        UPLOAD_PATH = 'v1/disk/resources/upload'

    class Resources(Enum):
        GET_DIR = 'v1/disk/resources'

    def __init__(self):
        super(YAHttpWorker, self).__init__('https://cloud-api.yandex.net',
                                           _ResourcesFactory.YA_TOKEN,
                                           'Yandex'
                                           )
        self.token = 'OAuth ' + self.token

    def upload_url(self, url, file_name):
        status_code, get_upload_url_result = self.__get_upload_url(file_name)
        if status_code != 409:
            self.__upload_file(url, file_name)
        return status_code

    def __get_upload_url(self, path):
        result = requests.get(self.join_url_path(self.base_api_url, self.Upload.UPLOAD_PATH.value),
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
        result = requests.post(self.join_url_path(self.base_api_url, self.Upload.UPLOAD_PATH.value),
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
        result = requests.put(self.join_url_path(self.base_api_url, self.Resources.GET_DIR.value),
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
        file_path = self.join_url_path(folder, file_name)
        print(f'Saving Log File:\nLocaly: {file_name}\nRemotely: {file_path}')
        status_code, upload_url = self.__get_upload_url(file_path)
        if not os.path.exists(_ResourcesFactory.LOG_DIR.value):
            os.mkdir(_ResourcesFactory.LOG_DIR.value)
        with open(self.join_url_path(_ResourcesFactory.LOG_DIR.value, file_name), 'w') as f:
            f.write(json.dumps(data))
        with open(self.join_url_path(_ResourcesFactory.LOG_DIR.value, file_name), 'rb') as f:
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

    class Type(Enum):
        FOLDER = 0
        FILE = 1

    def __init__(self):
        super(GoogleHttpWorker, self).__init__('https://www.googleapis.com',
                                               _ResourcesFactory.GOOGLE_TOKEN,
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

        if not os.path.exists(_ResourcesFactory.TMP_DIR.value):
            try:
                os.mkdir(_ResourcesFactory.TMP_DIR.value)
            except IOError:
                print('Warning: Could not create "tmp/" dir. This will lead to buffering Errors.'
                      'Please fix this before proceed.')

    def upload_file(self, file_url, name, parent_folder):
        file_existence = self.__check_existence(name, parent_folder, self.Type.FILE)
        if len(file_existence) != 0:
            return 409

        result = requests.get(file_url)
        result.raise_for_status()
        with open(self.join_url_path(_ResourcesFactory.TMP_DIR.value, name), 'wb') as f:
            f.write(result.content)

        file = MediaFileUpload(
            self.join_url_path(_ResourcesFactory.TMP_DIR.value, name),
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
        if search_type == self.Type.FOLDER or search_type is None:
            check_folder = self.service.files().list(
                q=f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{name}' and parents in '{root}'",
                fields="files(id, name, parents)"
            ).execute().get('files')
        elif search_type == self.Type.FILE:
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
        file_path = self.join_url_path(self.default_backup_dir, str(saved_dir_name), str(file_name))
        print(f'Saving Log File:\nLocaly: {file_name}\nRemotely: {file_path}')
        if not os.path.exists(_ResourcesFactory.LOG_DIR.value):
            os.mkdir(_ResourcesFactory.LOG_DIR.value)
        with open(self.join_url_path(_ResourcesFactory.LOG_DIR.value, file_name), 'w') as f:
            f.write(json.dumps(data))

        file = MediaFileUpload(
            self.join_url_path(_ResourcesFactory.LOG_DIR.value, file_name),
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
