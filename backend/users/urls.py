from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import CustomUserViewSet, FollowViewSet

app_name = "users"

router = DefaultRouter()

router.register("users", CustomUserViewSet, basename="users")
router.register(
    r"users/(?P<user_id>\d+)/subscribe", FollowViewSet, basename="subscribe"
)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include("djoser.urls")),
]
