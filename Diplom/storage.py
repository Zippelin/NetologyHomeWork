from httpreq import YAHttpWorker, GoogleHttpWorker
from datetime import datetime
import pathlib


class Storage:
    def __init__(self, requester, name):
        self.requester = requester
        self._upload_report = []
        self.name = name
        if self.requester.token == "":
            quit()
        print(f'\t{self.name} Token load Success')

    def _change_filename(self, file_name):
        file_name = str(file_name).split('.')
        file_name = f'{file_name[0]}_{str(datetime.now().strftime("%d-%m-%Y_%H.%M.%S"))}.{file_name[1]}'
        return file_name


class YAStorage(Storage):
    def __init__(self):
        super().__init__(YAHttpWorker(), 'Yandex Disk')

    def backup_photos(self, photos_data):
        photos_count = photos_data.pop('photos_count')
        progress_bar = ProgressBar(photos_count)
        root_dir = self.requester.create_dir()
        progress_bar.start()
        for user_id, albums in photos_data.items():
            user_dir = self.requester.create_dir(pathlib.PurePosixPath(root_dir, str(user_id)).__str__())
            for album, photos_list in albums.items():
                album_dir = self.requester.create_dir(pathlib.PurePosixPath(user_dir, str(album)).__str__())
                for photo in photos_list:
                    progress_bar.announce(str(photo['name']))
                    file_name = str(photo['name'])

                    status_code = self.requester.upload_url(photo['url'],
                                                            pathlib.PurePosixPath(album_dir, file_name).__str__())
                    if status_code == 409:
                        file_name = self._change_filename(file_name)
                        self.requester.upload_url(photo['url'],
                                                  pathlib.PurePosixPath(album_dir, file_name).__str__())
                    progress_bar.step()
                    self._upload_report.append({
                        'file_name': file_name,
                        'size': photo['size']
                    })
        self.requester.save_report(user_dir, self._upload_report)


class GoogleStorage(Storage):
    def __init__(self):
        super().__init__(GoogleHttpWorker(), 'Google Drive')

    def backup_photos(self, photos_data):
        photos_count = photos_data.pop('photos_count')
        progress_bar = ProgressBar(photos_count)
        app_root_id = self.requester.create_dir()   # create app root dir
        progress_bar.start()
        for user_id, albums in photos_data.items():
            user_dir_id = self.requester.create_dir(user_id, app_root_id)   # create user dir
            for album, photos in albums.items():
                album_id = self.requester.create_dir(album, user_dir_id)    # create album dir
                for photo in photos:
                    file_name = str(photo['name'])
                    progress_bar.announce(file_name)
                    status_code = self.requester.upload_file(photo['url'], photo['name'], album_id)
                    if status_code == 409:
                        file_name = self._change_filename(file_name)
                        _ = self.requester.upload_file(photo['url'], file_name, album_id)
                    progress_bar.step()

                    self._upload_report.append({
                        'file_name': file_name,
                        'size': photo['size']
                    })
        self.requester.save_report(user_dir_id, self._upload_report, user_id)


class ProgressBar:
    def __init__(self, length):
        self.width = 20
        self.length = length
        self.stp = 0
        self.files_list = []

    def start(self):
        print('Backup progress:')
        print('', end='\r[' + '_' * self.width + '] ' + str(0) + '%')

    def step(self):
        self.stp += 1
        real_percents = (self.stp / self.length) * 100
        print('', end='\r[' + '░' * (int((self.width * real_percents) / 100)) + '_' * (
                self.width - int((self.width * real_percents) / 100)) + '] ' + str(int(real_percents)) + '%')
        if real_percents == 100:
            print('\nBackup complete for:\n' + ' '.join([
                f'[{file}]'
                for file in self.files_list
            ]))
            print('Files Upload Complete\n')

    def announce(self, title):
        self.files_list.append(title)
        real_percents = (self.stp / self.length) * 100
        print('', end='\r[' + '░' * (int((self.width * real_percents) / 100)) + '_' * (
                self.width - int((self.width * real_percents) / 100)) + '] ' + str(int(real_percents)) + '%')