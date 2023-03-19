from rest_framework.routers import DefaultRouter

from api.views import (FavoriteRecipeViewSet, IngredientViewSet, RecipeViewSet,
                       ShoppingCartViewSet, TagViewSet)

v1_router = DefaultRouter()

v1_router.register("recipes", RecipeViewSet, basename="recipe")
v1_router.register("ingredients", IngredientViewSet, basename="ingredient")
v1_router.register("tags", TagViewSet, basename="tag")
v1_router.register(
    "shopping_cart", ShoppingCartViewSet, basename="shopping_cart"
)
v1_router.register("favorites", FavoriteRecipeViewSet, basename="favorite")
