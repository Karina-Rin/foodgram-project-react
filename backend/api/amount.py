from typing import TYPE_CHECKING

from recipes.models import AmountIngredient

if TYPE_CHECKING:
    from recipes.models import Ingredient


def create_ingredients_amounts(self, ingredients, recipe):
    AmountIngredient.objects.bulk_create(
        [
            AmountIngredient(
                ingredient=Ingredient.objects.get(id=ingredient["id"]),
                recipe=recipe,
                amount=ingredient["amount"],
            )
            for ingredient in ingredients
        ]
    )
