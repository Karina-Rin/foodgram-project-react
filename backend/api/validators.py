from string import hexdigits
from typing import TYPE_CHECKING, List, Optional

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

if TYPE_CHECKING:
    from recipes.models import Ingredient, Tag


@deconstructible
class MinLenValidator:
    min_len = 0
    field = "Переданное значение"
    message = f"\n{field} должно быть не менее {min_len} символов в длину.\n"

    def __init__(
        self,
        min_len: Optional[int] = None,
        field: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        if min_len is not None:
            self.min_len = min_len
        if field is not None:
            self.field = field
        if message is not None:
            self.message = message
        else:
            self.message = (
                f"{self.field} должно быть не менее "
                f"{self.min_len} символов в длину."
            )

    def validate(self, value: str) -> None:
        if len(value) < self.min_len:
            raise ValueError(self.message)

    def __call__(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Значение должно быть строкой")
        if len(value) < self.min_len:
            raise ValueError(self.message % (self.field, self.min_len))


def hex_color_validator(color: str) -> str:
    color = color.strip(" #")
    if len(color) not in (3, 6):
        raise ValidationError(
            f"HEX-код {color} неправильной длины ({len(color)})."
        )
    if not set(color).issubset(hexdigits):
        raise ValidationError(f"{color} не шестнадцатиричное.")
    if len(color) == 3:
        return f"#{color[0] * 2}{color[1] * 2}{color[2] * 2}".upper()
    return "#" + color.upper()


def tags_exist_validator(tags_ids: List[int or str], tag: "Tag") -> None:
    exists_tags = Tag.objects.filter(id__in=tags_ids)

    if len(exists_tags) != len(tags_ids):
        raise ValidationError(
            "Указанный тэг отсутствует в базе, обратитесь к администратору."
        )


def ingredients_exist_validator(
    ingredients: list, ingredient: "Ingredient"
) -> list:
    ings_ids = [None] * len(ingredients)

    for idx, ing in enumerate(ingredients):
        ingredients[idx]["amount"] = int(ingredients[idx]["amount"])
        if ingredients[idx]["amount"] < 1:
            raise ValidationError("Проверьте кол-во ингредиента")
        ings_ids[idx] = ing.pop("id", 0)

    ings_in_db = Ingredient.objects.filter(id__in=ings_ids).order_by("pk")
    ings_ids.sort()

    for idx, id in enumerate(ings_ids):
        ingredient: "Ingredient" = ings_in_db[idx]
        if ingredient.id != id:
            raise ValidationError(
                "Ингредиент отсутствует в базе, обратитесь к администратору."
            )

        ingredients[idx]["ingredient"] = ingredient
    return ingredients
