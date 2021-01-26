from httpreq import HttpRequester, ResourcesFactory
import requests


class UserProfile(HttpRequester):
    def __init__(self, user_id, api_base_path, token_file_path, api_name):
        self.user_id = user_id
        self.albums_list = []
        super(UserProfile, self).__init__(api_base_path, token_file_path, api_name)

    def get_albums(self, count=None):
        photos_count, albums = self._get_profile_data(self.user_id, count)
        return {self.user_id: albums,
                'photos_count': photos_count
                }

    def get_init_status(self):
        return self.get_status()

    def _get_profile_data(self, user_id, count=None):
        return [0, 0]


class VKProfile(UserProfile):

    __api_version = '5.126'
    ENDPOINT_GET_PHOTOS = 'photos.get'
    ENDPOINT_GET_USERS = 'users.get'
    ENDPOINT_GET_ALBUMS = 'photos.getAlbums'

    def __init__(self, user_id):
        super().__init__(user_id,
                         'https://api.vk.com/method',
                         ResourcesFactory.VK_TOKEN,
                         'VK'
                         )

    def _get_profile_data(self, user_id, count=None):
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
        result = requests.get(self.join_url_path(self.base_api_url, self.ENDPOINT_GET_PHOTOS),
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
        result = requests.get(self.join_url_path(self.base_api_url, self.ENDPOINT_GET_USERS),
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


class ODNProfile(UserProfile):
    def __init__(self, user_id,):
        super(ODNProfile, self).__init__(user_id,
                                         'https://api.ok.ru',
                                         ResourcesFactory.ODN_TOKEN,
                                         'Odnoklassniki'
                                         )


class InstaProfile(UserProfile):
    ENDPOINT_GET_MEDIA = 'media'

    def __init__(self, user_id):
        super().__init__(user_id,
                         'https://graph.instagram.com',
                         ResourcesFactory.INSTA_TOKEN,
                         'Instagram'
                         )

    def _get_profile_data(self, user_id, count=None):
        if not user_id.isdigit():
            return [0, 0]
        else:

            result = requests.get(self.join_url_path(self.base_api_url, user_id, self.ENDPOINT_GET_MEDIA),
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