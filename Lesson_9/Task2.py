import requests
import os

TOKEN_FILE = 'resources//token.txt'
UPLOAD_FILE_DIR = 'resources//data//'


class HttpFilesUploader:
    __base_url = 'https://cloud-api.yandex.net'
    __upload_file_url_path = 'v1/disk/resources/upload'

    def __init__(self, token):
        self.__token = token
        self.__auth_header = {
            'Authorization': f"OAuth {self.__token}"
        }

    def upload_file(self, file_name, binary_file):
        upload_url = self.join_url_path(self.__base_url, self.__upload_file_url_path)
        response = requests.get(upload_url,
                                params={
                                    'path': file_name,
                                    'overwrite': 'true'
                                },
                                headers=self.__auth_header
                                )
        response.raise_for_status()
        upload_url = response.json()['href']
        response = requests.put(upload_url,
                                files={'file': binary_file}
                                )
        response.raise_for_status()

    def join_url_path(self, *args):
        return '/'.join(args)


class YandexDiskFileSynchronizer:

    def __init__(self):
        with open('resources/token.txt') as f:
            self.fu_manager = HttpFilesUploader(f.read())

    def sync_dir(self, dir_name):
        files_list = self.__get_files_path_list(dir_name)
        for file in files_list:
            _, file_name = os.path.split(file)
            with open(file, 'rb') as f:
                self.fu_manager.upload_file(file_name, f)

    def __get_files_path_list(self, files_dir):
        result_files_path = []
        with os.scandir(files_dir) as dir_content:
            for item in dir_content:
                if item.is_file():
                    result_files_path.append(item.path)
        return result_files_path


if __name__ == '__main__':
    ya_file_manager = YandexDiskFileSynchronizer()
    ya_file_manager.sync_dir(UPLOAD_FILE_DIR)
