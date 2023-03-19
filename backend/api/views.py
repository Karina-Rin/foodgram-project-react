from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAdmin
from api.serializers import (IngredientSerializer, MiniRecipeSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             SubscribeSerializer, TagSerializer)
from api.utils import delete_for_actions, get_cart_txt, post_for_actions
from recipes.models import (Ingredient, IngredientAmount, Recipe,
                            RecipeFavorite, ShoppingCart, Subscribe, Tag)
from users.models import User


class SubscribeViewSet(viewsets.GenericViewSet):
    serializer_class = SubscribeSerializer
    queryset = User.objects.all()

    @action(
        detail=False,
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def subscriptions(self, request):
        user = self.request.user
        subscriptions = user.follower.all().values("author")
        result = User.objects.filter(id__in=subscriptions)
        page = self.paginate_queryset(result)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[
            IsAdmin,
        ],
    )
    def subscribe(self, request, pk):
        user = self.request.user
        author = get_object_or_404(User, pk=pk)
        serializer = self.get_serializer(author)

        if self.request.method == "POST":
            if user == author:
                raise serializers.ValidationError(
                    "Нельзя подписаться на самого себя!"
                )
            post_for_actions(user, author, Subscribe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            delete_for_actions(user, author, Subscribe)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ("^name",)


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = [
        IsAdmin,
    ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return RecipeCreateSerializer
        return RecipeSerializer


class FavoriteViewSet(viewsets.GenericViewSet):
    serializer_class = MiniRecipeSerializer
    queryset = Recipe.objects.all()

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[
            IsAdmin,
        ],
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


class ShoppingCartViewSet(viewsets.GenericViewSet):
    serializer_class = MiniRecipeSerializer
    queryset = Recipe.objects.all()

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[
            IsAdmin,
        ],
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
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientAmount.objects.filter(recipe__cart__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
        )
        return get_cart_txt(ingredients)
