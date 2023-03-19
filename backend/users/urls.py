from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import SubscribeViewSet

app_name = "users"

v1_router = DefaultRouter()

v1_router.register("users", SubscribeViewSet, basename="subscribe")


urlpatterns = [
    path("", include(v1_router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
