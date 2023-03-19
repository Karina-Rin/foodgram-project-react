import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Ingredient, IngredientAmount, Recipe, Tag
from users.models import User


class RegistrationUserSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        if self.context["request"].user.is_authenticated:
            user = get_object_or_404(
                User, username=self.context["request"].user
            )
            return user.follower.filter(author=obj.id).exists()
        return False


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=Ingredient.objects.all(),
                fields=("name", "measurement_unit"),
                message=("Такой ингредиент уже есть в базе."),
            )
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient.id"
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = IngredientAmount
        fields = ("id", "name", "measurement_unit", "amount")
        extra_kwargs = {
            "amount": {
                "min_value": None,
            },
        }


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):

    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source="ingredient_amount"
    )
    author = CustomUserSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        if self.context["request"].user.is_authenticated:
            user = get_object_or_404(
                User, username=self.context["request"].user
            )
            return user.recipe.filter(recipe=obj.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context["request"].user.is_authenticated:
            user = get_object_or_404(
                User, username=self.context["request"].user
            )
            return user.cart.filter(recipe=obj.id).exists()
        return False


class RecipeCreateSerializer(RecipeSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )

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
        extra_kwargs = {
            "cooking_time": {
                "min_value": None,
            },
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=("author", "name"),
                message="Рецепт с таким названием уже есть.",
            )
        ]

    @staticmethod
    def save_ingredients(recipe, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            current_ingredient = ingredient["ingredient"]["id"]
            current_amount = ingredient["amount"]
            ingredients_list.append(
                IngredientAmount(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=current_amount,
                )
            )
        IngredientAmount.objects.bulk_create(ingredients_list)

    def validate(self, data):
        if data["cooking_time"] <= 0:
            raise serializers.ValidationError(
                "Время приготовления не может быть < 1 минуты."
            )

        ingredients_list = []
        for ingredient in data["ingredient_amount"]:
            if ingredient["amount"] <= 0:
                raise serializers.ValidationError(
                    "Количество не может быть < 1."
                )
            ingredients_list.append(ingredient["ingredient"]["id"])

        if len(ingredients_list) > len(set(ingredients_list)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return data

    def create(self, validated_data):
        author = self.context["request"].user
        ingredients = validated_data.pop("ingredient_amount")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.add(*tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.image = validated_data.get("image", instance.image)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        ingredients = validated_data.pop("ingredient_amount")
        tags = validated_data.pop("tags")
        instance.tags.clear()
        instance.tags.add(*tags)
        instance.ingredients.clear()
        recipe = instance
        self.save_ingredients(recipe, ingredients)
        instance.save()
        return instance


class MiniRecipeSerializer(RecipeSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "cooking_time", "image")


class SubscribeSerializer(CustomUserSerializer):

    recipes = MiniRecipeSerializer(read_only=True, many=True)
    recipes_count = serializers.IntegerField(
        source="recipes.count", read_only=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
