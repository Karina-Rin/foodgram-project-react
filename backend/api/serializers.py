from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, IngredientAmount, Recipe, Tag
from users.models import Follow, User


class CommonFollowSerializer(serializers.SerializerMetaclass):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, follow__id=obj.id
        ).exists()


class FavoriteRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        extra_kwargs = {
            "name": {"required": False},
            "measurement_unit": {"required": False},
        }


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit",
    )

    class Meta:
        model = IngredientAmount
        fields = ("id", "name", "measurement_unit", "amount")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
        extra_kwargs = {
            "name": {"required": False},
            "slug": {"required": False},
            "color": {"required": False},
        }


class RegistrationUserSerializer(CommonFollowSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_subscription",
            "password",
        )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("name", None)
        kwargs.setdefault("bases", ())
        kwargs.setdefault("attrs", {})
        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        result = super(RegistrationUserSerializer, self).to_representation(obj)
        result.pop("password", None)
        return result


class UsersSerializer(UserSerializer):
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
        request = self.context.get("request")
        if not request.user or request.user.is_anonymous:
            return False
        subcribe = request.user.follower.filter(author=obj)
        return subcribe.exists()


class RecipeSerializer(serializers.ModelSerializer):
    author = UsersSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(many=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )


class IngredientAmountRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")

    class Meta:
        model = IngredientAmount
        fields = ("id", "amount")


class ShoppingCartSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountRecipeSerializer(
        source="ingredient_recipes", many=True
    )
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "image",
            "text",
            "ingredients",
            "tags",
            "cooking_time",
            "is_in_shopping_cart",
            "is_favorited",
        )

    def validate_ingredients(self, value):
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            id_to_check = ingredient["ingredient"]["id"]
            ingredient_to_check = Ingredient.objects.filter(id=id_to_check)
            if not ingredient_to_check.exists():
                raise serializers.ValidationError("Этого продукта нет в базе!")
            ingredients_list.append(ingredient_to_check)
        return value

    def uniq_ingredients_and_tags(self, data):
        ingredients = data["ingredients"]
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient["id"]
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    {"ingredients": "Ингредиенты должны быть уникальными!"}
                )
            ingredients_list.append(ingredient_id)
            amount = ingredient["amount"]
            if int(amount) <= 0:
                raise serializers.ValidationError(
                    {"amount": "Количество ингредиента должно быть >=1!"}
                )
        tags = data["tags"]
        if len(ingredients_list) > len(set(ingredients_list)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        if not tags:
            raise serializers.ValidationError(
                {"tags": "Необходимо выбрать хотя бы один тэг!"}
            )
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError(
                    {"tags": "Тэги должны быть уникальными!"}
                )
            tags_list.append(tag)
            if len(tags_list) > len(set(tags_list)):
                raise serializers.ValidationError(
                    "Тэги не должны повторяться."
                )
        cooking_time = data["cooking_time"]
        if int(cooking_time) <= 0:
            raise serializers.ValidationError(
                {"cooking_time": "Время приготовления должно быть больше 0!"}
            )

        return data

    def create(self, validated_data):
        author = validated_data.get("author")
        tags_data = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredient_recipes")
        Recipe.objects.create(author=author, **validated_data)
        self.uniq_ingredients_and_tags(tags_data, ingredients)

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredient_recipes")
        Follow.objects.filter(recipe=instance).delete()
        IngredientAmount.objects.filter(recipe=instance).delete()
        instance = self.uniq_ingredients_and_tags(
            tags_data,
            ingredients,
        )
        super().update(instance, validated_data)
        instance.save()
        return instance
