from collections import OrderedDict
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.query import QuerySet
from django.db.transaction import atomic
from drf_extra_fields.fields import Base64ImageField
from recipes.models import AmountIngredient, Ingredient, Recipe, Tag
from rest_framework.serializers import (ListSerializer, ModelSerializer,
                                        SerializerMethodField)

if TYPE_CHECKING:
    from recipes.models import Ingredient

User = get_user_model()


class FilterRecipesLimitSerializer(ListSerializer):
    def to_representation(self, data):
        if "recipes_limit" not in self.context.get("request").query_params:
            return super().to_representation(data)
        recipes_limit = int(
            self.context.get("request").query_params.get("recipes_limit")
        )
        return super().to_representation(data)[:recipes_limit]


class ShortRecipeSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = "id", "name", "image", "cooking_time"
        read_only_fields = ("__all__",)
        list_serializer_class = FilterRecipesLimitSerializer


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
        )
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ("is_subscribed",)

    def get_is_subscribed(self, obj: User) -> bool:
        user = self.context.get("view").request.user

        if user.is_anonymous or (user == obj):
            return False

        return user.subscriptions.filter(author=obj).exists()

    def create(self, validated_data: dict) -> User:
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class SubscribeSerializer(UserSerializer):
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("__all__",)

    def get_is_subscribed(*args) -> bool:
        return True

    def get_recipes_count(self, obj: User) -> int:
        return obj.recipes.count()


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
        read_only_fields = ("__all__",)

    def validate(self, data: OrderedDict) -> OrderedDict:
        for attr, value in data.items():
            data[attr] = value.sttrip(" #").upper()

        return data


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"
        read_only_fields = ("__all__",)


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = (
            "is_favorite",
            "is_shopping_cart",
        )

    def create_ingredients_amounts(self, ingredients, recipe):
        AmountIngredient.objects.bulk_create(
            [
                AmountIngredient(
                    ingredients=Ingredient.objects.get(id=ingredient["id"]),
                    recipe=recipe,
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients
            ],
        )

    def get_ingredients(self, recipe: Recipe) -> QuerySet:
        return recipe.ingredients.values(
            "id", "name", "measurement_unit", amount=F("recipe__amount")
        )

    def get_is_favorited(self, recipe: Recipe) -> bool:
        user = self.context.get("view").request.user

        if user.is_anonymous:
            return False

        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        user = self.context.get("view").request.user

        if user.is_anonymous:
            return False

        return user.carts.filter(recipe=recipe).exists()

    def validate(self, data: OrderedDict) -> OrderedDict:
        tags_ids: list[int] = self.initial_data.get("tags")
        ingredients = self.initial_data.get("ingredients")

        if not tags_ids or not ingredients:
            raise ValidationError("Недостаточно данных.")

        data.update(
            {
                "tags": tags_ids,
                "ingredients": ingredients,
                "author": self.context.get("request").user,
            }
        )
        return data

    @atomic
    def create(self, validated_data: dict) -> Recipe:
        tags: list[int] = validated_data.pop("tags")
        ingredients: dict[int, tuple] = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(ingredients, recipe)
        return recipe

    @atomic
    def update(self, recipe: Recipe, validated_data: dict):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")

        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            self.create_ingredients_amounts(ingredients, recipe)

        recipe.save()
        return recipe
