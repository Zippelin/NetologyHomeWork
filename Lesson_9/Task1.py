import  requests
from enum import  Enum
from pprint import  pprint

HEROES_LIST = []

class BestSuperHeroFinder:

    class PowerStat(Enum):
        INTELLIGENCE = 'intelligence'
        STRENGTH = 'strength'
        SPEED = 'speed'
        DURABILITY = 'durability'
        POWER = 'power'
        COMBAT = 'combat'

    def __init__(self):
        self.filtered_sp_list = []
        self.sp_connector = SuperHeroDataRequester()

    def get_sorted_sp_by_stat(self, power_stat, *sp_list):
        if isinstance(power_stat, self.PowerStat):
            for sp_hero in sp_list:
                self.filtered_sp_list.append({
                    'name': sp_hero,
                    'power_stats': self.sp_connector.get_sp_stats_list(sp_hero)
                })
            self.filtered_sp_list.sort(key=lambda x: int(x['power_stats'][power_stat.value]), reverse=True)
            return self.filtered_sp_list
        else:
            raise Exception('First value mandatory should be type of "PowerStat" class')


class SuperHeroDataRequester:
    __token = '2619421814940190'
    __base_path = 'https://superheroapi.com/api'
    __power_stat_path_chunk = 'powerstats'
    __name_path_chunk = 'search'

    def __init__(self):
        self.__base_path = self.join_url_path(self.__base_path, self.__token)

    def get_sp_stats_list(self, sp_name):
        return self.__get_sp_stats_by_name(sp_name)

    def __get_sp_stats_by_name(self, sp_name):
        stats_url = self.join_url_path(self.__base_path, self.__name_path_chunk, sp_name)
        response = requests.get(stats_url)
        response.raise_for_status()
        result = response.json()
        for superHero in result['results']:
            if superHero['name'] == sp_name:
                return superHero['powerstats']

    def join_url_path(self, *args):
        return '/'.join(args)

if __name__ == '__main__':
    sp_comparer = BestSuperHeroFinder()
    sorted_sp = sp_comparer.get_sorted_sp_by_stat(sp_comparer.PowerStat.INTELLIGENCE, 'Hulk', 'Captain America', 'Thanos')
    pprint(sorted_sp)