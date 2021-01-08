import requests
from enum import Enum
from pprint import pprint

TOKEN_FILE = 'resources//token.txt'


class HttpRequestBuilder:
    __base_api_url = 'https://api.vk.com/method'
    __api_version = '5.126'
    __base_url = 'https://vk.com'

    class Users(Enum):
        GET = 'users.get'

    class Friends(Enum):
        GET = 'friends.get'

    def __init__(self):
        with open(TOKEN_FILE, 'r') as f:
            self.__token = f.read()

    def get_user(self, user_id):
        if user_id is not None:
            url = self.join_url_path(self.__base_api_url, self.Users.GET.value)
            result = requests.get(url,
                                  params={
                                        'access_token': self.__token,
                                        'v': self.__api_version,
                                        'user_ids': user_id,
                                  })
            result.raise_for_status()
            return result.json()['response'][0]

    def get_friends_list(self, user_id):
        if user_id is not None:
            url = self.join_url_path(self.__base_api_url, self.Friends.GET.value)
            result = requests.get(url,
                                  params={
                                      'access_token': self.__token,
                                      'v': self.__api_version,
                                      'user_id': user_id
                                  })
            result.raise_for_status()
            result = result.json()
            if result.get('error') is None:
                return result['response']['items']
            else:
                return [
                    value['value']
                    for value in result['error']['request_params']
                    if value['key'] == 'user_id'
                ]

    def join_url_path(self, *args):
        return '/'.join(args)

    def get_user_url(self, user_id):
        if user_id is not None:
            return self.join_url_path(self.__base_url, 'id' + str(user_id))


class VKUser:
    def __init__(self, user_id):
        self.id = None
        self.http_requester = HttpRequestBuilder()
        result = self.http_requester.get_user(user_id)
        for k, v in result.items():
            self.__dict__[k] = v
        self.friends_list = self.get_friends_list()

    def get_user_info(self):
        return {
            k: self.__dict__[k]
            for k in self.__dict__
            if not isinstance(self.__dict__[k], HttpRequestBuilder)
        }

    def get_friends_list(self):
        return self.http_requester.get_friends_list(self.id)

    def __and__(self, other):
        friends_interception = set(self.get_friends_list()) & set(other.get_friends_list())
        return [
            VKUser(friend)
            for friend in friends_interception
        ]

    def __str__(self):
        return self.http_requester.get_user_url(self.id)

    def __repr__(self):
        return f'id: {self.id}, url: {self.__str__()}'


if __name__ == '__main__':
    vk1 = VKUser('552934290')
    pprint(vk1.get_user_info())

    vk2 = VKUser('stomumcom')
    pprint(vk2.get_user_info())

    print(vk1 & vk2)
    print(vk1)