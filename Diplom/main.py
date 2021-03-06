from profile import VKProfile, InstaProfile, ODNProfile
from storage import YAStorage, GoogleStorage
import shutil

if __name__ == '__main__':
    ya_storage = YAStorage()
    google_storage = GoogleStorage()

    profiler_menu_factory = {
        '1': VKProfile,
        '2': ODNProfile,
        '3': InstaProfile,
    }

    storage_menu_factory = {
        '1': ya_storage,
        '2': google_storage
    }

    want_next = True
    print()
    while want_next:
        print('Welcome to photo backupper for social networks')
        print('System Status:')

        storage = profiler = count_filter = ''

        while profiler not in profiler_menu_factory.keys():
            profiler = input('Please enter network\n\t1 = Vk\n\t2 = Odnoklasniki\n\t3 = Instagram\n:>')

        while storage not in storage_menu_factory.keys():
            storage = input('Choose backup platform\n\t1 = Yandex Disk\n\t2 = Google Drive\n:>')

        profiler = profiler_menu_factory[profiler]
        storage = storage_menu_factory[storage]

        user_id = input('Enter User Id:\n:>')

        print('System Status:')
        profiler = profiler(user_id)

        while not count_filter.isdigit():
            count_filter = input('Enter size slice limit( 0 - no limits)\n:>')

        albums = profiler.get_albums(int(count_filter))

        if albums['photos_count'] == 0:
            print('No photos found, maybe profile is private.')
        else:
            storage.backup_photos(albums)

        shutil.rmtree('tmp/*', ignore_errors=True)
        want_next = ''
        while want_next.lower() not in ['yes', 'no', '0', '1', 'да', 'нет', 'н', 'д', 'n', 'y']:
            want_next = input('Do you wan to continue? (yes\\no)')
        if want_next.lower() == 'no' or \
                want_next.lower() == 'n' or \
                want_next.lower() == '0' or \
                want_next.lower() == 'нет' or \
                want_next.lower() == 'н':
            want_next = False
            shutil.rmtree('tmp/', ignore_errors=True)
