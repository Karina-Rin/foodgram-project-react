from typing import TYPE_CHECKING, Dict, Tuple

from recipes.models import AmountIngredient, Recipe

if TYPE_CHECKING:
    from recipes.models import Ingredient


def recipe_ingredients_set(
    recipe: Recipe, ingredients: Dict[int, Tuple["Ingredient", int]]
) -> None:

    objs = []

    for ingredient, amount in ingredients.items():
        objs.append(
            AmountIngredient(
                recipe=recipe, ingredients=ingredient[0], amount=amount[1]
            )
        )

    AmountIngredient.objects.bulk_create(objs)
