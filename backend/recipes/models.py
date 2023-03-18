from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

max_legth = settings.MAX_LEGTH

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name="Тег",
        help_text="Введите название тега",
        max_length=max_legth,
        db_index=True,
        unique=True,
    )
    color = models.CharField(
        verbose_name="HEX-код",
        help_text="Введите HEX-код цвета тега",
        max_length=7,
        default="#FF0000",
        null=True,
        unique=True,
        validators=[
            RegexValidator(
                "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
                message="Поле должно содержать HEX-код выбранного цвета.",
            )
        ],
    )
    slug = models.SlugField(
        verbose_name="Slug тэга",
        help_text="Введите текстовый идентификатор тега",
        max_length=max_legth,
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} (цвет: {self.color})"


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name="Название ингредиента",
        help_text="Введите название ингредиента",
        max_length=max_legth,
    )
    measurement_unit = models.CharField(
        verbose_name="Единицы измерения",
        max_length=max_legth,
        help_text="Введите единицы измерения",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_name_measurement_unit",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name="author_recipe",
        verbose_name="Автор публикации",
        help_text="Выберите автора рецепта",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Название рецепта",
        help_text="Введите название рецепта",
        max_length=max_legth,
    )
    image = models.ImageField(
        verbose_name="Изображение",
        help_text="Выберите изображение рецепта",
        upload_to="recipes/images",
        null=True,
        blank=True,
    )
    text = models.TextField(
        verbose_name="Описание рецепта",
        help_text="Введите описание рецепта",
        default="",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name="recipes",
        verbose_name="Ингредиенты для приготовления блюда по рецепту",
        help_text="Выберите ингредиенты рецепта",
        through='IngredientAmount',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тег",
        related_name="recipes",
        help_text="Выберите тэг рецепта.",
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления",
        help_text="Введите время приготовления",
        validators=(MinValueValidator(1, "Значение не может быть 0"),),
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-id",)

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="recipe",
        verbose_name="Рецепт",
        help_text="Выберите рецепт",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name="ingredient",
        verbose_name="Ингредиент",
        help_text="Добавить ингредиенты рецепта в корзину",
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        help_text="Введите количество ингредиентов",
        default=1,
        null=False,
        blank=False,
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient"), name="unique ingredient"
            )
        ]

    def __str__(self):
        return (
            f"В рецепте {self.recipe.name} {self.amount} "
            f"{self.ingredient.measurement_unit} {self.ingredient.name}"
        )


class RecipeFavorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name="favorites",
        verbose_name="Автор списка избранного",
        help_text="Выберите автора",
        on_delete=models.CASCADE,
    )
    favorite_recipe = models.ForeignKey(
        Recipe,
        related_name="favorite_recipe",
        verbose_name="Избранный рецепт",
        help_text="Выберите рецепт",
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "favorite_recipe"), name="unique favourite"
            )
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.user} -> {self.favorite_recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name="shopping_cart",
        verbose_name="Автор списка покукок",
        help_text="Выберите автора",
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="shopping_cart",
        verbose_name="Рецепты в списке покупок",
        help_text="Выберите рецепты для добавления продуктов в корзину",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_cart",
            )
        ]
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"

    def __str__(self):
        return (
            f"ShoppingCart("
            f"id={self.id}, "
            f"user={self.user.username}, "
            f"recipe={self.recipe.name})"
        )


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        related_name="follower",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Выберите пользователя для подписки",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор рецепта",
        related_name="followed_by",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Выберите автора для подписки",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            UniqueConstraint(fields=["user", "author"], name="follow_unique")
        ]
