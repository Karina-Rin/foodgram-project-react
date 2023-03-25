from typing import TYPE_CHECKING, Dict, List, Tuple

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

if TYPE_CHECKING:
    from recipes.models import Ingredient, Tag


@deconstructible
class MinLenValidator:
    pass


def tags_exist_validator(tags_ids: List[int or str], Tag: "Tag") -> None:
    exists_tags = Tag.objects.filter(id__in=tags_ids)

    if len(exists_tags) != len(tags_ids):
        raise ValidationError("Указан несуществующий тэг")


def ingredients_validator(
    ingredients: List[Dict[str, str or int]],
    Ingredient: "Ingredient",
) -> Dict[int, Tuple["Ingredient", int]]:

    valid_ings = {}

    for ing in ingredients:
        if not (isinstance(ing["amount"], int) or ing["amount"].isdigit()):
            raise ValidationError("Неправильное количество ингредиента")

        amount = valid_ings.get(ing["id"], 0) + int(ing["amount"])
        valid_ings[ing["id"]] = amount

    if not valid_ings:
        raise ValidationError("Неправильные ингредиенты")

    db_ings = Ingredient.objects.filter(pk__in=valid_ings.keys())
    if not db_ings:
        raise ValidationError("Неправильные ингредиенты")

    for ing in db_ings:
        valid_ings[ing.pk] = (ing, valid_ings[ing.pk])

    return
