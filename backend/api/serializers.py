from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    IngredientAmount,
    Recipe,
    RecipeFavorite,
    ShoppingCart,
    Tag,
)
from users.models import Follow, User


class CommonFollowSerializer(metaclass=serializers.SerializerMetaclass):
    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        if Follow.objects.filter(
            user=request.user, following__id=obj.id
        ).exists():
            return True
        else:
            return False


class CommonRecipeSerializer(metaclass=serializers.SerializerMetaclass):
    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        if RecipeFavorite.objects.filter(
            user=request.user, recipe__id=obj.id
        ).exists():
            return True
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request.user.is_anonymous:
            return False
        if ShoppingCart.objects.filter(
            user=request.user, recipe__id=obj.id
        ).exists():
            return True
        else:
            return False


class CommonCount(metaclass=serializers.SerializerMetaclass):
    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()


class RegistrationUserSerializer(UserCreateSerializer, CommonFollowSerializer):
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
        write_only_fields = ("password",)
        read_only_fields = ("id",)
        extra_kwargs = {"is_subscription": {"required": False}}

    def to_representation(self, obj):
        result = super(RegistrationUserSerializer, self).to_representation(obj)
        result.pop("password", None)
        return result


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


class IngredientAmountRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")

    class Meta:
        model = IngredientAmount
        fields = ("id", "amount")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
        extra_kwargs = {
            "name": {"required": False},
            "slug": {"required": False},
            "color": {"required": False},
        }


class FavoriteRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )


class ShoppingCartSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )


class RecipeSerializer(serializers.ModelSerializer, CommonFollowSerializer):
    author = RegistrationUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(
        source="ingredient_recipes", many=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField()

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


class RecipeCreateSerializer(
    serializers.ModelSerializer, CommonFollowSerializer
):
    author = RegistrationUserSerializer(read_only=True)
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
            if len(ingredients_list) > len(set(ingredients_list)):
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяться."
                )
            ingredients_list.append(ingredient_id)
            amount = ingredient["amount"]
            if int(amount) <= 0:
                raise serializers.ValidationError(
                    {"amount": "Количество ингредиента должно быть >=1!"}
                )
        tags = data["tags"]
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
        recipe = Recipe.objects.create(
            author=author,
            **validated_data,
        )
        self.uniq_ingredients_and_tags(tags_data, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredient_recipes")
        Follow.objects.filter(recipe=instance).delete()
        IngredientAmount.objects.filter(recipe=instance).delete()
        instance = self.uniq_ingredients_and_tags(
            tags_data, ingredients, instance
        )
        super().update(instance, validated_data)
        instance.save()
        return instance


class RecipeMinifieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "cooking_time", "image")


class FollowSerializer(
    serializers.ModelSerializer, CommonFollowSerializer, CommonCount
):
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_follow",
            "recipes",
            "recipes_count",
        )

    def get_recipes_limit(self, obj):
        request = self.context.get("request")
        if request.GET.get("recipes_limit"):
            recipes_limit = int(request.GET.get("recipes_limit"), 0)
            queryset = Recipe.objects.filter(author__id=obj.id).order_by("id")[
                :recipes_limit
            ]
        else:
            queryset = Recipe.objects.filter(author__id=obj.id).order_by("id")
        return RecipeMinifieldSerializer(queryset, many=True).data
