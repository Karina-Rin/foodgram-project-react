from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (FavoriteRecipeViewSet, IngredientViewSet, RecipeViewSet,
                       ShoppingCartViewSet, TagViewSet)

app_name = "api"

router = DefaultRouter()

router.register("recipes", RecipeViewSet, basename="recipes")
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register(
    r"recipes/(?P<recipe_id>\d+)/favorite",
    FavoriteRecipeViewSet,
    basename="favorite",
)
router.register(
    r"recipes/(?P<recipe_id>\d+)/shopping_cart",
    ShoppingCartViewSet,
    basename="shoppingcart",
)

urlpatterns = [
    path("", include(router.urls)),
]
