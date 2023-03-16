from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.mixins import ListCreateDeleteViewSet
from api.permissions import IsAdmin
from api.serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             SetPasswordSerializer, ShoppingCartSerializer,
                             SubscribeSerializer, TagSerializer,
                             UserCreateSerializer, UserReadSerializer)
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
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action == "set_password":
            return SetPasswordSerializer
        if self.action == "create":
            return UserCreateSerializer
        return UserReadSerializer

    def get_permissions(self):
        if self.action == "me":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = Subscribe.objects.filter(user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={"request": request},
        )
        return self.get_paginated_response(serializer.data)


class SubscribeViewSet(ListCreateDeleteViewSet):
    serializer_class = SubscribeSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return self.queryset.filter(user=self.request.user, author_id=user_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["author_id"] = self.kwargs.get("user_id")
        return context

    def perform_create(self, serializer):
        user_id = self.kwargs.get("user_id")
        serializer.save(
            user=self.request.user, author=get_object_or_404(User, id=user_id)
        )

    @action(methods=("delete",), detail=True)
    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Subscribe.objects.filter(
            user=request.user, author_id=user_id
        ).exists():
            return Response(
                {"errors": "Вы не были подписаны на автора"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription = get_object_or_404(
            Subscribe, user=request.user, author_id=user_id
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteRecipeViewSet(ListCreateDeleteViewSet):
    serializer_class = FavoriteRecipeSerializer

    def get_queryset(self):
        return RecipeFavorite.objects.filter(user=self.request.user.id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["recipe_id"] = self.kwargs.get("recipe_id")
        return context

    def perform_create(self, serializer):
        recipe_id = self.kwargs.get("recipe_id")
        recipe = get_object_or_404(Recipe, id=recipe_id)

        serializer.save(
            user=self.request.user,
            favorite_recipe=recipe,
        )

    @action(methods=("delete",), detail=True)
    def delete(self, request, recipe_id):
        try:
            favorite = request.user.favorite.get(favorite_recipe_id=recipe_id)
        except RecipeFavorite.DoesNotExist:
            return Response(
                {"errors": "Рецепт не в избранном"},
                status=status.HTTP_404_NOT_FOUND,
            )

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(ListCreateDeleteViewSet):
    serializer_class = ShoppingCartSerializer

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user.id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["recipe_id"] = self.kwargs.get("recipe_id")
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            recipe=get_object_or_404(Recipe, id=self.kwargs.get("recipe_id")),
        )

    @action(methods=("delete",), detail=True)
    def delete(self, request, recipe_id):
        queryset = request.user.shopping_cart.select_related("recipe")
        shopping_cart = get_object_or_404(queryset, recipe_id=recipe_id)
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = IsAdmin
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        pagination_class=None,
    )
    def download_file(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                "В корзине пусто", status=status.HTTP_400_BAD_REQUEST
            )

        ingredient_name = "recipe__recipe__ingredient__name"
        ingredient_unit = "recipe__recipe__ingredient__measurement_unit"
        recipe_amount = "recipe__recipe__amount"
        amount_sum = "recipe__recipe__amount__sum"
        cart = (
            user.shopping_cart.select_related("recipe")
            .values(ingredient_name, ingredient_unit)
            .annotate(Sum(recipe_amount))
            .order_by(ingredient_name)
        )
        if not cart:
            return Response("Корзина пуста", status=status.HTTP_404_NOT_FOUND)

        text = "Список покупок:\n\n"
        for item in cart:
            text += (
                f"{item[ingredient_name]} ({item[ingredient_unit]})"
                f" — {item[amount_sum]}\n"
            )
        response = HttpResponse(text, content_type="text/plain")
        filename = "shopping_list.txt"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
