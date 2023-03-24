from api.views import (
    BaseAPIRootView,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet,
)
from django.urls import include, path
from rest_framework.routers import DefaultRouter


app_name = "api"


class DefaultRouter(DefaultRouter):
    APIRootView = BaseAPIRootView


v1_router = DefaultRouter()
v1_router.register("users", UserViewSet, "users")
v1_router.register("tags", TagViewSet, "tags")
v1_router.register("ingredients", IngredientViewSet, "ingredients")
v1_router.register("recipes", RecipeViewSet, "recipes")

urlpatterns = (
    path("", include(v1_router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
)
