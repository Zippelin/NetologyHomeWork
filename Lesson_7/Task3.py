import os
import codecs

# константа, чтобы легче проверить было, указав путь до папки  файлами
SOURCE_FILES_DIR = 'resources//Task3//'
OUTPUT_FILE = os.path.join(SOURCE_FILES_DIR, 'out.txt')


class FilesContentSorter:
    def __init__(self, files_dir):
        self.files_dir = files_dir

    def sort_and_save(self):
        sorted_raw_files_list = self.__sort()
        self.__save(sorted_raw_files_list)

    def __save(self, sorted_raw_files_list):
        output_file_content = ''
        for file in sorted_raw_files_list:
            output_file_content += f'{file["file_name"]}\n'         \
                                   f'{file["file_lines_count"]}\n'  \
                                   f'{file["file_content"]}\n'

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(output_file_content)

    def __sort(self):
        raw_files_list = self.__read_files()
        raw_files_list.sort(key=lambda file: file['file_lines_count'])
        return raw_files_list

    def __read_files(self):
        raw_files_content = []
        files_path = self.__get_files_path_list()
        for file_path in files_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.readlines()
                raw_files_content.append({
                    'file_name': os.path.basename(f.name),
                    'file_lines_count': len(file_content),
                    'file_content': ''.join(file_content)
                })
        return raw_files_content

    def __get_files_path_list(self):
        result_files_path = []
        with os.scandir(self.files_dir) as dir_content:
            for item in dir_content:
                if item.is_file():
                    result_files_path.append(item.path)
        return result_files_path


if __name__ == '__main__':
    sorted_files_content = FilesContentSorter(SOURCE_FILES_DIR)
    sorted_files_content.sort_and_save()