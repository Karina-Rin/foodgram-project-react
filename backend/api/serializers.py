from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from djoser.serializers import (PasswordSerializer, UserCreateSerializer,
                                UserSerializer)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Ingredient, IngredientAmount, Recipe,
                            RecipeFavorite, ShoppingCart, Subscribe, Tag)
from users.models import User

User = get_user_model()


class UserReadSerializer(UserSerializer):
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
        return (
            self.context.get("request").user.is_authenticated
            and Subscribe.objects.filter(
                user=self.context.get("request").user, author=obj
            ).exists()
        )


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password")
        required_fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )


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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(
        many=True,
        source="recipe",
        required=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        return (
            self.context.get("request").user.is_authenticated
            and RecipeFavorite.objects.filter(
                user=self.context.get("request").user, favorite_recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get("request").user.is_authenticated
            and ShoppingCart.objects.filter(
                user=self.context.get("request").user, recipe=obj
            ).exists()
        )


class IngredientAmountRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ("id", "amount")


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    ingredients = IngredientAmountSerializer(many=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recipe
        fields = "__all__"
        extra_kwargs = {
            "tags": {
                "error_messages": {
                    "does_not_exist": (
                        "Ошибка в Тэге, id = {pk_value} " "не существует"
                    )
                }
            }
        }

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
        Subscribe.objects.filter(recipe=instance).delete()
        IngredientAmount.objects.filter(recipe=instance).delete()
        instance = self.uniq_ingredients_and_tags(
            tags_data,
            ingredients,
        )
        super().update(instance, validated_data)
        instance.save()
        return instance


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        extra_kwargs = {
            "name": {"required": False},
            "measurement_unit": {"required": False},
        }


class SetPasswordSerializer(PasswordSerializer):
    current_password = serializers.CharField(
        required=True, label="Текущий пароль"
    )

    def validate(self, data):
        user = self.context.get("request").user
        if data["new_password"] == data["current_password"]:
            raise serializers.ValidationError(
                {"new_password": "Пароли не должны совпадать"}
            )
        check_current = check_password(data["current_password"], user.password)
        if check_current is False:
            raise serializers.ValidationError(
                {"current_password": "Введен неверный пароль"}
            )
        return data


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscribeSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="author.email", read_only=True)
    id = serializers.IntegerField(source="author.id", read_only=True)
    username = serializers.CharField(source="author.username", read_only=True)
    first_name = serializers.CharField(
        source="author.first_name", read_only=True
    )
    last_name = serializers.CharField(
        source="author.last_name", read_only=True
    )
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="author.recipe.count")

    class Meta:
        model = Subscribe
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

    def validate(self, data):
        user = self.context.get("request").user
        author = self.context.get("author_id")
        if user.id == int(author):
            raise serializers.ValidationError(
                {"errors": "Нельзя подписаться на самого себя"}
            )
        if Subscribe.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {"errors": "Вы уже подписаны на данного пользователя"}
            )
        return data

    def get_recipes(self, obj):
        recipes = obj.author.recipe.all()
        return SubscribeRecipeSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        subscribe = Subscribe.objects.filter(
            user=self.context.get("request").user, author=obj.author
        )
        if subscribe:
            return True
        return False


class FavoriteRecipeSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField(
        source="favorite_recipe.id",
    )
    name = serializers.ReadOnlyField(
        source="favorite_recipe.name",
    )
    image = serializers.CharField(
        source="favorite_recipe.image",
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source="favorite_recipe.cooking_time",
    )

    class Meta:
        model = RecipeFavorite
        fields = ("id", "name", "image", "cooking_time")

    def validate(self, data):
        user = self.context.get("request").user
        recipe = self.context.get("recipe_id")
        if RecipeFavorite.objects.filter(
            user=user, favorite_recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                {"errors": "Рецепт уже в избранном"}
            )
        return data


class ShoppingCartSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField(
        source="recipe.id",
    )
    name = serializers.ReadOnlyField(
        source="recipe.name",
    )
    image = serializers.CharField(
        source="recipe.image",
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source="recipe.cooking_time",
    )

    class Meta:
        model = ShoppingCart
        fields = ("id", "name", "image", "cooking_time")

    def validate(self, data):
        user = self.context.get("request").user
        recipe = self.context.get("recipe_id")
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {"errors": "Рецепт уже добавлен в список покупок"}
            )
        return data
