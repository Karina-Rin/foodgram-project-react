from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (FavoriteViewSet, IngredientsViewSet, RecipesViewSet,
                       ShoppingCartViewSet, SubscribeViewSet, TagsViewSet)

v1_router = DefaultRouter()

v1_router.register("users", SubscribeViewSet, basename="subscribe")
v1_router.register("recipes", RecipesViewSet, basename="recipe")
v1_router.register("ingredients", IngredientsViewSet, basename="ingredient")
v1_router.register("tags", TagsViewSet, basename="tag")
v1_router.register(
    "shopping_cart", ShoppingCartViewSet, basename="shopping_cart"
)
v1_router.register("favorites", FavoriteViewSet, basename="favorite")


urlpatterns = [
    path("", include(v1_router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
