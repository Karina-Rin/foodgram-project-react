from http import HTTPStatus

from api.filters import IngredientSearchFilter, RecipeFilters
from api.permissions import IsAdmin
from api.serializers import (CommonFollowSerializer, FavoriteRecipeSerializer,
                             IngredientSerializer, RecipeCreateSerializer,
                             RecipeSerializer, RegistrationUserSerializer,
                             ShoppingCartSerializer, TagSerializer)
from api.utils import delete_for_actions, get_cart_txt, post_for_actions
from django.db.models import Sum
from django.shortcuts import get_list_or_404, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Ingredient, IngredientAmount, Recipe,
                            RecipeFavorite, ShoppingCart, Tag)
from reportlab.lib.pagesizes import A4
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import Follow, User


class UserView(UserViewSet):
    serializer_class = RegistrationUserSerializer

    def get_queryset(self):
        return User.objects.all()


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = CommonFollowSerializer
    permission_classes = IsAdmin

    def get_queryset(self):
        return get_list_or_404(User, following__user=self.request.user)

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get("users_id")
        user = get_object_or_404(User, id=user_id)
        Follow.objects.create(user=request.user, following=user)
        return Response(HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        author_id = self.kwargs["users_id"]
        user_id = request.user.id
        subscribe = get_object_or_404(
            Follow, user__id=user_id, following__id=author_id
        )
        subscribe.delete()
        return Response(HTTPStatus.NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = IsAdmin
    filter_class = RecipeFilters
    filter_backends = [
        DjangoFilterBackend,
    ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeSerializer
        else:
            return RecipeCreateSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = IsAdmin
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, IngredientSearchFilter)
    pagination_class = None
    search_fields = [
        "^name",
    ]


class BaseFavoriteCartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create_shopping_cart(self, request, *args, **kwargs):
        recipe_id = int(self.kwargs["recipes_id"])
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.model.objects.create(user=request.user, recipe=recipe)
        return Response(HTTPStatus.CREATED)

    def delete_shopping_cart(self, request, *args, **kwargs):
        recipe_id = self.kwargs["recipes_id"]
        user_id = request.user.id
        object = get_object_or_404(
            self.model, user__id=user_id, recipe__id=recipe_id
        )
        object.delete()
        return Response(HTTPStatus.NO_CONTENT)


class RecipeFavoriteViewSet(BaseFavoriteCartViewSet):
    serializer_class = FavoriteRecipeSerializer
    queryset = RecipeFavorite.objects.all()
    model = RecipeFavorite

    @action(
        detail=True, methods=["post", "delete"], permission_classes=IsAdmin
    )
    def favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = self.get_serializer(recipe)

        if self.request.method == "POST":
            post_for_actions(user, recipe, RecipeFavorite)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            delete_for_actions(user, recipe, RecipeFavorite)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(BaseFavoriteCartViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    model = ShoppingCart
    permission_classes = IsAdmin

    @action(
        detail=True, methods=["post", "delete"], permission_classes=IsAdmin
    )
    def shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = self.get_serializer(recipe)

        if self.request.method == "POST":
            post_for_actions(user, recipe, ShoppingCart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            delete_for_actions(user, recipe, ShoppingCart)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=[
            "get",
        ],
        permission_classes=IsAdmin,
    )
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientAmount.objects.filter(recipe__cart__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
        )
        return get_cart_txt(ingredients)
