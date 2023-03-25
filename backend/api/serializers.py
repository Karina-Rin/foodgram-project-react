from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, Tag
from rest_framework import status
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from users.models import Subscribe

User = get_user_model()


class ShortRecipeSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = "id", "name", "image", "cooking_time"
        read_only_fields = ("__all__",)


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

    def validate(self, data):
        author = self.instance
        user = self.context.get("request").user
        if Subscribe.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail="Вы уже подписаны на этого пользователя!",
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise ValidationError(
                detail="Вы не можете подписаться на самого себя!",
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
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

    def get_ingredients(self, obj):
        recipe = obj
        ingredients = recipe.ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=F("ingredient__amount"),
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError(
                {"ingredients": "Нужен хотя бы один ингредиент!"}
            )
        ingredients_list = []
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item["id"])
            if ingredient in ingredients_list:
                raise ValidationError(
                    {"ingredients": "Ингридиенты не могут повторяться!"}
                )
            if int(item["amount"]) <= 0:
                raise ValidationError(
                    {"amount": "Количество ингредиента должно быть больше 0!"}
                )
            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError({"tags": "Нужно выбрать хотя бы один тег!"})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError(
                    {"tags": "Теги должны быть уникальными!"}
                )
            tags_list.append(tag)
        return value

    @transaction.atomic
    def create_ingredients_amounts(self, ingredients, recipe):
        Ingredient.objects.bulk_create(
            [
                Ingredient(
                    ingredient=Ingredient.objects.get(id=ingredient["id"]),
                    recipe=recipe,
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(recipe=recipe, ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients_amounts(
            recipe=instance, ingredients=ingredients
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get("request")
        context = {"request": request}
        return RecipeSerializer(instance, context=context).data
