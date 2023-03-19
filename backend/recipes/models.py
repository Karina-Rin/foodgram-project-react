from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

max_legth = settings.MAX_LEGTH

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name="Тэг",
        help_text="Введите название тэга",
        max_length=max_legth,
        db_index=True,
        unique=True,
    )
    color = models.CharField(
        verbose_name="HEX-код",
        help_text="Введите HEX-код цвета тэга",
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
        help_text="Введите текстовый идентификатор тэга",
        max_length=max_legth,
        unique=True,
    )

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("name",)

    def __str__(self):
        return self.name


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
        ordering = ("name",)
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
        through="IngredientAmount",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тэг",
        related_name="recipes",
        help_text="Выберите тэг рецепта.",
    )
    cooking_time = models.IntegerField(
        verbose_name="Время приготовления",
        help_text="Введите время приготовления",
        validators=(MinValueValidator(1, "Значение не может <= 0"),),
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания"
    )

    class Meta:
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["author", "name"], name="unique_author_name"
            )
        ]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeFavorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name="recipe",
        verbose_name="Автор списка избранного",
        help_text="Выберите автора",
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="recipe",
        verbose_name="Избранный рецепт",
        help_text="Выберите рецепт",
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_favourite"
            )
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        ordering = ("id",)


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="ingredient_amount",
        verbose_name="Рецепт",
        help_text="Выберите рецепт",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name="ingredient_amount",
        verbose_name="Ингредиент",
        help_text="Добавить ингредиенты рецепта в корзину",
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        verbose_name="Количество",
        help_text="Введите количество ингредиентов",
        validators=[
            MinValueValidator(1, "Количество не может быть < 1."),
        ],
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"

    def __str__(self):
        return f"{self.ingredient}: {self.amount}"


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
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_cart",
            )
        ]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

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
        related_name="following",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Выберите автора для подписки",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            UniqueConstraint(
                fields=["user", "author"], name="unique_user_author"
            )
        ]

    def __str__(self):
        return f"Подписка {self.user.username} на {self.author.username}"
