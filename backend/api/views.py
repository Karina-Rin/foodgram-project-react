from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.pagination import Pagination
from api.permissions import IsAdmin
from api.serializers import (IngredientSerializer, RecipeCreateSerializer,
                             RecipeSerializer, SubscribeSerializer,
                             TagSerializer)
from api.utils import delete_for_actions, post_for_actions
from recipes.models import (Ingredient, Recipe, RecipeFavorite, ShoppingCart,
                            Subscribe, Tag)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filterset_class = IngredientSearchFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class UserViewSet(UserViewSet):
    pagination_class = Pagination

    @action(
        detail=True,
        permission_classes=[IsAuthenticated],
        methods=["POST", "DELETE"],
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if self.request.method == "POST":
            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на данного пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow = Subscribe.objects.create(user=user, author=author)
            serializer = SubscribeSerializer(
                follow, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if Subscribe.objects.filter(user=user, author=author).exists():
            follow = get_object_or_404(Subscribe, user=user, author=author)
            follow.delete()
            return Response(
                "Подписка успешно удалена", status=status.HTTP_204_NO_CONTENT
            )
        if user == author:
            return Response(
                {"errors": "Нельзя отписаться от самого себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"errors": "Вы не подписаны на данного пользователя"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False, permission_classes=[IsAuthenticated], methods=["GET"]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = Pagination

    def get_queryset(self):
        is_favorited = self.request.query_params.get("is_favorited")
        if is_favorited is not None and int(is_favorited) == 1:
            return Recipe.objects.filter(favorites__user=self.request.user)
        is_in_shopping_cart = self.request.query_params.get(
            "is_in_shopping_cart"
        )
        if is_in_shopping_cart is not None and int(is_in_shopping_cart) == 1:
            return Recipe.objects.filter(cart__user=self.request.user)
        return Recipe.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            "Рецепт успешно удален", status=status.HTTP_204_NO_CONTENT
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action != "create":
            return (IsAdmin(),)
        return super().get_permissions()

    @action(
        detail=True,
        methods=["POST", "DELETE"],
    )
    def favorite(self, request, pk):
        if self.request.method == "POST":
            return post_for_actions(
                request, pk, RecipeFavorite, SubscribeSerializer
            )
        return delete_for_actions(request, pk, RecipeFavorite)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return post_for_actions(
                request, pk, ShoppingCart, SubscribeSerializer
            )
        return delete_for_actions(request, pk, ShoppingCart)
