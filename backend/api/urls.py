from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, FollowViewSet, IngredientViewSet,
                       RecipeFavoriteViewSet, RecipeViewSet,
                       ShoppingCartViewSet, TagViewSet)

router = DefaultRouter()
router.register("users", CustomUserViewSet, basename="users")
router.register("recipes", ShoppingCartViewSet, basename="shopping_cart")
router.register("recipes", RecipeFavoriteViewSet, basename="favorite")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register(
    r"users/(?P<user_id>\d+)/follows", FollowViewSet, basename="follows"
)
router.register(
    r"recipes/(?P<recipe_id>\d+)/favorite",
    RecipeFavoriteViewSet,
    basename="favorite",
)
urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
