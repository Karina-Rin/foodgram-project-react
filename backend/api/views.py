from datetime import datetime as dt
from typing import List
from urllib.parse import unquote

from api.mixins import AddDelViewMixin
from api.paginators import PageLimitPagination
from api.permissions import AdminOrReadOnly, AuthorStaffOrReadOnly
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             ShortRecipeSerializer, SubscribeSerializer,
                             TagSerializer)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import F, Q, QuerySet, Sum
from django.http.response import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Ingredient, Recipe, RecipeFavorite, ShoppingCart,
                            Tag)
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
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
    permission_classes = (AdminOrReadOnly,)

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
    permission_classes = (AdminOrReadOnly,)


class RecipeViewSet(ModelViewSet, AddDelViewMixin):
    queryset = Recipe.objects.select_related("author")
    serializer_class = RecipeSerializer
    permission_classes = (AuthorStaffOrReadOnly,)
    pagination_class = PageLimitPagination
    add_serializer = ShortRecipeSerializer

    def get_queryset(self) -> QuerySet[Recipe]:
        queryset = self.queryset

        tags: list = self.request.query_params.getlist("tags")
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        author: str = self.request.query_params.get("author")
        if author:
            queryset = queryset.filter(author=author)

        if self.request.user.is_anonymous:
            return queryset

        is_in_shopping_cart: str = self.request.query_params.get(
            "is_in_shopping_cart"
        )
        if is_in_shopping_cart in symbol_true_search.value:
            queryset = queryset.filter(
                in_shopping_carts__user=self.request.user
            )
        elif is_in_shopping_cart in symbol_false_search.value:
            queryset = queryset.exclude(
                in_shopping_carts__user=self.request.user
            )

        is_favorit: str = self.request.query_params.get("is_favorited")
        if is_favorit in symbol_true_search.value:
            queryset = queryset.filter(in_favorites__user=self.request.user)
        if is_favorit in symbol_false_search.value:
            return queryset.exclude(in_favorites__user=self.request.user)

        return queryset

    @action(
        methods=action_methods,
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request: WSGIRequest, pk: int or str) -> Response:
        return self._add_del_obj(pk, RecipeFavorite, Q(recipe__id=pk))

    @action(
        methods=action_methods,
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request: WSGIRequest, pk: int or str) -> Response:
        return self._add_del_obj(pk, ShoppingCart, Q(recipe__id=pk))

    @action(methods=("get",), detail=False)
    def download_shopping_cart(self, request: WSGIRequest) -> Response:
        user = self.request.user
        if not user.shopping_cart.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        filename = f"{user.username}_shopping_list.txt"
        shopping_list = [
            f"Список покупок для:\n\n{user.first_name}\n"
            f"{dt.now().strftime(date_time_format)}\n"
        ]

        ingredients = (
            Ingredient.objects.filter(
                recipe__recipe__in_shopping_carts__user=user
            )
            .values("name", measurement=F("measurement_unit"))
            .annotate(amount=Sum("recipe__amount"))
        )

        for ing in ingredients:
            shopping_list.append(
                f'{ing["name"]}: {ing["amount"]} {ing["measurement"]}'
            )
        shopping_list.append("\nПодсчёт в Foodgram")
        shopping_list = "\n".join(shopping_list)
        response = HttpResponse(
            shopping_list, content_type="text.txt; charset=utf-8"
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
