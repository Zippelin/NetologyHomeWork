from profile import VKProfile, InstaProfile, ODNProfile
from storage import YAStorage, GoogleStorage
import time
import shutil

# aa = VKProfile('552934290')
#
# albums = aa.get_albums()
# #print(albums)
#
# bb = YAStorage()
# bb.backup_photos(albums)
# if __name__ == '__main__':
#     for i in range(100):
#         print("", end=f"\rPercentComplete: {i} %")
#         time.sleep(0.2)


class AwesomeBackupper:
    def __init__(self):
        self.vk_profiler = None
        self.odn_profiler = None
        self.insta_profiler = None
        self.ya_storage = YAStorage()
        self.google_storage = GoogleStorage()

        self.profiler_menu_factory = {
            '1': VKProfile,
            '2': ODNProfile,
            '3': InstaProfile,
        }

        self.storage_menu_factory = {
            '1': self.ya_storage,
            '2': self.google_storage
        }

    def start(self):
        want_next = True
        while want_next:
            print('Welcome to photo backupper for social networks')
            print('System Status:')
            for k, v in self.storage_menu_factory.items():
                storage_status = v.get_init_status()
                if not storage_status:
                    return
            print()

            storage = ''
            profiler = ''
            count_filter = ''

            while profiler not in self.profiler_menu_factory.keys():
                profiler = input('Please enter network\n\t1 = Vk\n\t2 = Odnoklasniki\n\t3 = Instagram\n:>')

            while storage not in self.storage_menu_factory.keys():
                storage = input('Choose backup platform\n\t1 = Yandex Disk\n\t2 = Google Drive\n:>')

            profiler = self.profiler_menu_factory[profiler]
            storage = self.storage_menu_factory[storage]

            user_id = input('Enter User Id:\n')

            profiler = profiler(user_id)

            print('System Status:')
            if not profiler.get_init_status():
                return

            while not count_filter.isdigit():
                count_filter = input('Enter size slice limit( 0 - no limits)\n:>')

            if count_filter == '0':
                count_filter = None
            else:
                count_filter = int(count_filter)

            albums = profiler.get_albums(count_filter)
            if albums['photos_count'] == 0:
                print('No photos found, maybe profile is private.')
            else:
                storage.backup_photos(albums)

            shutil.rmtree('tmp/', ignore_errors=True)
            want_next = ''
            while want_next.lower() not in ['yes', 'no', '0', '1', 'да', 'нет', 'н', 'д', 'n', 'y']:
                want_next = input('Do you wan to continue? (yes\\no)')
            if want_next.lower() == 'no' or \
                    want_next.lower() == 'n' or \
                    want_next.lower() == '0' or \
                    want_next.lower() == 'нет' or \
                    want_next.lower() == 'н':
                want_next = False


if __name__ == '__main__':
    awb = AwesomeBackupper()
    awb.start()
