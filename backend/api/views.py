from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.mixins import ListCreateDeleteViewSet
from api.permissions import IsAdmin
from api.serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             RegistrationUserSerializer,
                             ShoppingCartSerializer, SubscribeSerializer,
                             TagSerializer)
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
    serializer_class = RegistrationUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False, methods=["get"], permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeViewSet(ListCreateDeleteViewSet):
    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["author_id"] = self.kwargs.get("user_id")
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            author=get_object_or_404(User, id=self.kwargs.get("user_id")),
        )

    @action(methods=("delete",), detail=True)
    def delete(self, request, user_id):
        get_object_or_404(User, id=user_id)
        if not Subscribe.objects.filter(
            user=request.user, author_id=user_id
        ).exists():
            return Response(
                {"errors": "Вы не были подписаны на автора"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        get_object_or_404(
            Subscribe, user=request.user, author_id=user_id
        ).delete()
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=("delete",), detail=True)
    def delete(self, request, recipe_id):
        try:
            favorite = request.user.favorite.get(favorite_recipe_id=recipe_id)
            favorite.delete()
        except RecipeFavorite.DoesNotExist:
            return Response(
                {"errors": "Рецепта нет в избранном"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
        recipe = get_object_or_404(Recipe, id=self.kwargs.get("recipe_id"))
        if recipe.author != self.request.user:
            return Response(
                {
                    "error": "Вы не можете добавить в корзину рецепт, "
                    "который не принадлежит вам"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer.save(user=self.request.user, recipe=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=("delete",), detail=True)
    def delete(self, request, recipe_id):
        queryset = request.user.shopping_cart.select_related("recipe")
        shopping_cart = get_object_or_404(queryset, recipe_id=recipe_id)
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        status_code = None
        error_msg = None

        if isinstance(exc, Http404):
            error_msg = "Страница не найдена"
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, PermissionDenied):
            error_msg = "Отказано в разрешении"
            status_code = status.HTTP_401_UNAUTHORIZED
        else:
            error_msg = "Плохой запрос"
            status_code = status.HTTP_400_BAD_REQUEST

        return Response({"error": error_msg}, status=status_code)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdmin)
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
