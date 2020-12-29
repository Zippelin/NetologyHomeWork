import re
from pprint import pprint

# константа, чтобы легче проверить было, указав путь до Вашего файла
RECIPES_FILEPATH = 'resources//Task1.txt'


class RecipesParser:
    ingredient_parse_template = r'^(?P<ingredient_name>[А-я ]*) . (?P<quantity>\d*) . (?P<measure>[А-я.]*)$|\n'

    def __init__(self, file_path):
        self.recipes_file_path = file_path
        self.recipes = {}

    def parse(self):
        with open(self.recipes_file_path, 'r', encoding='utf-8') as f:
            split_recipes = re.split(r'\n\n', f.read())
            if len(split_recipes) > 0:
                for recipe in split_recipes:
                    recipe_parse_result = self.__parse_recipe(recipe)
                    self.recipes[recipe_parse_result['recipe_name']] = recipe_parse_result['recipe_ingredient_list']
        return self.recipes

    def __parse_recipe(self, recipe):
        result_recipe_dict = {}
        recipe = recipe.splitlines()
        recipe_name = recipe.pop(0)
        _ = recipe.pop(0)
        result_recipe_dict['recipe_name'] = recipe_name
        result_recipe_dict['recipe_ingredient_list'] = []
        for ingredient in recipe:
            result = re.match(self.ingredient_parse_template, ingredient).groupdict()
            result['quantity'] = int(result['quantity'])
            result_recipe_dict['recipe_ingredient_list'].append(result)
        return result_recipe_dict

    def get_shop_list_by_dishes(self, dishes, person_count):
        result_ingredients_count = {}
        for dish in dishes:
            filtered_ingredients = self.recipes[dish]
            for ingredient in filtered_ingredients:
                if result_ingredients_count.get(ingredient['ingredient_name']) is None:
                    result_ingredients_count[ingredient['ingredient_name']] = {'measure': ingredient['measure'], 'quantity': ingredient['quantity'] * person_count}
                else:
                    result_ingredients_count[ingredient['ingredient_name']] += {'measure': ingredient['measure'], 'quantity': ingredient['quantity'] * person_count}

        return result_ingredients_count


if __name__ == '__main__':
    recipes = RecipesParser(RECIPES_FILEPATH)
    parsed_recipes = recipes.parse()
    pprint(parsed_recipes)
    print('\nИнгредиенты для закупки:')
    pprint(recipes.get_shop_list_by_dishes(['Запеченный картофель', 'Омлет'], 2))