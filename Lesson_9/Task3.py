import requests
import datetime
import time
from pprint import pprint

SEARCH_PERIOD = 2
MAX_SEARCH_PAGES = 2
REQUEST_DELAY = 0.5

class StackOverflowSearcher:
    __base_url = 'https://api.stackexchange.com/2.2'
    __search_url = 'search/advanced'

    def search(self, **kwargs):
        if isinstance(kwargs.get('fromdate'), int):
            from_date = (datetime.datetime.now() - datetime.timedelta(days=SEARCH_PERIOD)).date()
        else:
            from_date = ''
        page = 1
        search_url = self.join_url_path(self.__base_url, self.__search_url)
        params = {
            'tagged':   kwargs.get('tagged') if kwargs.get('tagged') != None else '',
            'site':     'stackoverflow',
            'sort':     kwargs.get('sort') if kwargs.get('sort') != None else '',
            'order':    kwargs.get('order') if kwargs.get('order') != None else '',
            'fromdate': from_date,
            'page':     page,
        }
        has_more = True
        titles_list = []
        while has_more:
            print('Requesting page: ', page)
            response =requests.get(search_url,
                                   params=params)
            response.raise_for_status()
            response = response.json()
            titles_list += [
                item['title']
                for item in response['items']
            ]
            has_more = response['has_more']
            if page == MAX_SEARCH_PAGES:
                has_more = False
            page += 1
            time.sleep(REQUEST_DELAY)

        return titles_list

    def join_url_path(self, *args):
        return '/'.join(args)


if __name__ == "__main__":
    searcher = StackOverflowSearcher()
    search_result = searcher.search(tagged='Python', sort='creation', order='desc', fromdate=SEARCH_PERIOD)
    pprint(search_result)