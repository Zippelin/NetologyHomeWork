import json
import xml.etree.ElementTree as ET
import  os
import collections

RESOURCE_DIR = 'resources//'
XML_SAMPLE_FILE_NAME = 'newsafr.xml'
JSON_SAMPLE_FILE_NAME = 'newsafr.json'

class FileReader():
    __words_len_filter = 6

    def __init__(self, files_path):
        self.file_path = files_path

    def read_json(self):
        deserialized_json = self.__load_json()
        return self.__get_most_popular_theme_word(deserialized_json, parse_mode='json')

    def __get_most_popular_theme_word(self, data, parse_mode=None):
        if parse_mode == 'json':
            theme_title_list = [
                item['title'].split()
                for item in data['rss']['channel']['items']
            ]
        elif parse_mode == 'xml':
            root = data.getroot()
            theme_title_list = [
                news.text.split()
                for news in root.iter('title')
                ]
        else:
            return None
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

    def read_xml(self):
        tree = self.__load_xml()
        return self.__get_most_popular_theme_word(tree, parse_mode='xml')


    def __load_json(self):
        with open(self.file_path, encoding='utf-8') as fp:
            return json.load(fp)

    def __load_xml(self):
        return ET.parse(self.file_path)

if __name__ == '__main__':
    most_popular_json_words = FileReader(os.path.join(RESOURCE_DIR, JSON_SAMPLE_FILE_NAME))
    most_popular_json_words = most_popular_json_words.read_json()
    print('Json result:\n', most_popular_json_words)

    print()

    most_popular_xml_words = FileReader(os.path.join(RESOURCE_DIR, XML_SAMPLE_FILE_NAME))
    most_popular_xml_words = most_popular_xml_words.read_xml()
    print('XML result:\n', most_popular_xml_words)