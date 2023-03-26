from typing import List
from urllib.parse import unquote

from api.mixins import AddDelViewMixin
from api.paginators import PageLimitPagination
from api.permissions import OwnerOrReadOnly
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             ShortRecipeSerializer, SubscribeSerializer,
                             TagSerializer)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, Sum
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Carts, Favorites, Ingredient, Recipe, Tag
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.models import Subscribe

date_time_format = settings.DATE_TIME_FORMAT
action_methods = settings.ACTION_METHODS
symbol_true_search = settings.SYMBOL_TRUE_SEARCH
symbol_false_search = settings.SYMBOL_FALSE_SEARCH

User = get_user_model()


class BaseAPIRootView(APIRootView):
    """API"""


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    pagination_class = PageLimitPagination
    add_serializer = SubscribeSerializer
    permission_classes = (DjangoModelPermissions,)

    @action(
        methods=action_methods,
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request: WSGIRequest, id: int or str) -> Response:
        return self._add_del_obj(id, Subscribe, Q(author__id=id))

    @action(methods=("get",), detail=False)
    def subscriptions(self, request: WSGIRequest) -> Response:
        if self.request.user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)

        pages = self.paginate_queryset(
            User.objects.filter(subscribers__user=self.request.user)
        )
        serializer = SubscribeSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get_queryset(self) -> List[Ingredient]:
        name: str = self.request.query_params.get("name")
        if name:
            if name[0] == "%":
                name = unquote(name)
            else:
                name = name.translate(
                    str.maketrans(
                        "qwertyuiop[]asdfghjkl;'zxcvbnm,./",
                        "йцукенгшщзхъфывапролджэячсмитьбю.",
                    )
                )
            name = name.lower()
            start_queryset = list(self.queryset.filter(name__istartswith=name))
            ingridients_set = set(start_queryset)
            cont_queryset = self.queryset.filter(name__icontains=name)
            start_queryset.extend(
                [ing for ing in cont_queryset if ing not in ingridients_set]
            )
            return start_queryset

        return self.queryset


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet, AddDelViewMixin):
    queryset = Recipe.objects.select_related("author")
    serializer_class = RecipeSerializer
    permission_classes = (OwnerOrReadOnly,)
    pagination_class = PageLimitPagination
    add_serializer = ShortRecipeSerializer

    def add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {"errors": "Рецепт уже добавлен!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"errors": "Рецепт уже удален!"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=action_methods,
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        if request.method == "POST":
            return self.add_to(Favorites, request.user, pk)
        else:
            return self.delete_from(Favorites, request.user, pk)

    @action(
        methods=action_methods,
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return self.add_to(Carts, request.user, pk)
        else:
            return self.delete_from(Carts, request.user, pk)

    @action(
        detail=False,
        methods=["get"],
        url_name="download_shopping_cart",
        url_path="download_shopping_cart",
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user
        queryset = (
            Carts.objects.filter(user=user)
            .values(
                "recipe__ingredients__name",
                "recipe__ingredients__measurement_unit",
            )
            .annotate(Sum("recipe__amountingredient__amount"))
            .order_by("recipe__ingredients__name")
        )

        shopping_list = ["Список покупок:\n\n"]
        for item in queryset:
            name = item["recipe__ingredients__name"].capitalize()
            measurement_unit = item["recipe__ingredients__measurement_unit"]
            amount = item["recipe__amountingredient__amount__sum"]
            shopping_list.append(f"{name} ({measurement_unit}) — {amount};\n")

        response = HttpResponse(shopping_list)
        response["Content-Type"] = "text/plain"
        response[
            "Content-Disposition"
        ] = 'attachment; filename="shopping_cart.txt"'
        return response
