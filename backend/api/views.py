from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.mixins import ListCreateDeleteViewSet
from api.permissions import IsAdmin
from api.serializers import (
    FavoriteRecipeSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    SetPasswordSerializer,
    ShoppingCartSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserReadSerializer,
)
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeFavorite,
    ShoppingCart,
    Subscribe,
    Tag,
)

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
    queryset = Subscribe.objects.all()

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
        if not Subscribe.objects.filter(
            user=request.user, author_id=user_id
        ).exists():
            return Response(
                {"errors": "Вы не были подписаны на автора"},
                status=status.HTTP_404_NOT_FOUND,
            )

        subscription = get_object_or_404(
            Subscribe, user=request.user, author_id=user_id
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            user=self.request.user,
            author=get_object_or_404(User, id=self.kwargs.get("user_id")),
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        Subscribe.objects.filter(
            user=request.user, author_id=self.kwargs.get("user_id")
        ).exists()


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
