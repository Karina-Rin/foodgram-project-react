from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (FavoriteRecipeViewSet, IngredientViewSet, RecipeViewSet,
                       ShoppingCartViewSet, SubscribeViewSet, TagViewSet)

app_name = "api"

v1_router = DefaultRouter()

v1_router.register("recipes", RecipeViewSet, basename="recipes")
v1_router.register("tags", TagViewSet, basename="tags")
v1_router.register("ingredients", IngredientViewSet, basename="ingredients")
v1_router.register(
    "shopping_cart", ShoppingCartViewSet, basename="shopping_cart"
)
v1_router.register("in_favorites", FavoriteRecipeViewSet, basename="favorite")
v1_router.register(
    r"users/(?P<user_id>\d+)/subscribe", SubscribeViewSet, basename="subscribe"
)

urlpatterns = [
    path("", include(v1_router.urls)),
]
