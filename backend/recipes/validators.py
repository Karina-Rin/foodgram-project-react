from rest_framework.validators import ValidationError as RFError

from recipes.models import Ingredient, Tag


def validate_time(value):
    if value < 1:
        raise RFError(["Время не может быть меньше 1 минуты."])


def validate_ingredients(data):
    if not data:
        raise RFError({"ingredients": ["Обязательное поле."]})
    if len(data) < 1:
        raise RFError({"ingredients": ["Не переданы ингредиенты."]})
    unique_ingredients = set()
    for ingredient in data:
        id = ingredient.get("id")
        if not id:
            raise RFError({"ingredients": ["Отсутствует id ингредиента."]})
        if id in unique_ingredients:
            raise RFError(
                {"ingredients": ["Нельзя дублировать имена ингредиентов."]}
            )
        unique_ingredients.add(id)
        if not Ingredient.objects.filter(id=id).exists():
            raise RFError({"ingredients": ["Ингредиента нет в Базе."]})
        amount = ingredient.get("amount")
        if amount < 1:
            raise RFError({"amount": ["Количество не может быть менее 1."]})
    return data
