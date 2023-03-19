from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (FavoriteRecipeViewSet, IngredientViewSet, RecipeViewSet,
                       ShoppingCartViewSet, SubscribeViewSet, TagViewSet)

v1_router = DefaultRouter()

v1_router.register("users", SubscribeViewSet, basename="subscribe")
v1_router.register("recipes", RecipeViewSet, basename="recipe")
v1_router.register("ingredients", IngredientViewSet, basename="ingredient")
v1_router.register("tags", TagViewSet, basename="tag")
v1_router.register(
    "shopping_cart", ShoppingCartViewSet, basename="shopping_cart"
)
v1_router.register("favorites", FavoriteRecipeViewSet, basename="favorite")


urlpatterns = [
    path("", include(v1_router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
