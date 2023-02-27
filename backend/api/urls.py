from api.views import (
    IngredientViewSet,
    RecipeFavoriteViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    TagViewSet,
    FollowViewSet,
)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("users", FollowViewSet, basename="wollow")
router.register("recipes", ShoppingCartViewSet, basename="shopping_cart")
router.register("recipes", RecipeFavoriteViewSet, basename="favorite")
router.register("recipes", RecipeViewSet)
router.register("tags", TagViewSet)
router.register("ingredients", IngredientViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
