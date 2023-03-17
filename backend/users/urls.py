from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import SubscribeViewSet, UserViewSet

app_name = "users"

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register(
    r"users/(?P<user_id>\d+)/subscribe", SubscribeViewSet, basename="subscribe"
)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
