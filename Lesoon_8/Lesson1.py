import json
import xml
import  os
from pprint import pprint
import collections

RESOURCE_DIR = 'resources//'

class FileReader():
    __words_len_filter = 6

    def __init__(self, files_path):
        self.file_path = files_path

    def read_json(self):
        deserialized_json = self.__load_json()
        most_popular_word = self.__get_most_popular_theme_word(deserialized_json)
        print(most_popular_word)

    def __get_most_popular_theme_word(self, data_dict):
        theme_title_list = [
            item['title'].split()
            for item in data_dict['rss']['channel']['items']
        ]
        theme_words_list = [
            word
            for title in theme_title_list
            for word in title if len(word) > self.__words_len_filter
        ]

        counter = collections.Counter(theme_words_list)
        theme_words_list = sorted(counter.most_common(10), key=lambda x: x[1], reverse=True)

        return [
            word[0]
            for word in theme_words_list
        ]

    def __read_xml(self):
        pass


    def __load_json(self):
        with open(self.file_path, encoding='utf-8') as fp:
            return json.load(fp)

ff = FileReader(os.path.join(RESOURCE_DIR, 'newsafr.json'))

ff.read_json()