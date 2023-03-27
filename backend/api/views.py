from datetime import datetime as dt
from typing import List
from urllib.parse import unquote

from api.mixins import AddDelViewMixin
from api.paginators import PageLimitPagination
from api.permissions import OwnerOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    SubscribeSerializer,
    TagSerializer,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import F, Q, Sum
from django.http.response import HttpResponse
from django.shortcuts import render
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Carts, Favorites, Ingredient, Recipe, Tag
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.models import Subscribe, User

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

    def author_detail(self, request, author_id):
        author = User.objects.get(id=author_id)
        recipes = Recipe.objects.filter(author=author)

        show_all = False
        if len(recipes) > 3:
            recipes = recipes[:3]
            show_all = True

        context = {
            "author": author,
            "recipes": recipes,
            "show_more": not show_all,
        }
        return render(request, "author_detail.html", context)


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


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet, AddDelViewMixin):
    queryset = Recipe.objects.select_related("author")
    serializer_class = RecipeSerializer
    permission_classes = (OwnerOrReadOnly,)
    pagination_class = PageLimitPagination
    add_serializer = ShortRecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()

        if not self.request.query_params:
            return queryset

        tags = self.request.query_params.getlist("tags")
        if tags is not None:
            slug = Tag.objects.filter(slug__in=tags).all()
            recipes = (
                Recipe.objects.filter(tags__in=slug).values("id").distinct()
            )
            queryset = queryset.filter(id__in=recipes)

        if self.request.user.is_anonymous:
            return queryset

        author_id = self.request.query_params.get("author")
        if author_id is not None:
            queryset = queryset.filter(author_id=author_id).all()

        is_in_cart: str = self.request.query_params.get("is_favorited")
        if is_in_cart in symbol_true_search:
            queryset = queryset.filter(in_carts__user=self.request.user)
        elif is_in_cart in symbol_false_search:
            queryset = queryset.exclude(in_carts__user=self.request.user)

        is_favorit: str = self.request.query_params.get("is_favorited")
        if is_favorit in symbol_true_search:
            queryset = queryset.filter(in_favorites__user=self.request.user)
        if is_favorit in symbol_false_search:
            queryset = queryset.exclude(in_favorites__user=self.request.user)

        return queryset

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

    @action(methods=("get",), detail=False)
    def download_shopping_cart(self, request: WSGIRequest) -> Response:
        user = self.request.user
        if not user.carts.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        filename = f"{user.username}_shopping_list.txt"
        shopping_list = [
            f"Список покупок для:\n\n{user.first_name}\n"
            f"{dt.now().strftime(date_time_format)}\n"
        ]

        ingredients = (
            Ingredient.objects.filter(recipe__recipe__in_carts__user=user)
            .values("name", measurement=F("measurement_unit"))
            .annotate(amount=Sum("recipe__amount"))
        )

        for ing in ingredients:
            shopping_list.append(
                f'{ing["name"]}: {ing["amount"]} {ing["measurement"]}'
            )
        shopping_list.append("\nВыгружено из Foodgram")
        shopping_list = "\n".join(shopping_list)
        response = HttpResponse(
            shopping_list, content_type="text.txt; charset=utf-8"
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
