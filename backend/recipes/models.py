from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name="Название",
        help_text="Введите название тега",
        max_length=settings.MAX_LEGTH,
        unique=True,
    )
    color = models.CharField(
        verbose_name="HEX-код",
        help_text="Введите цвет тега",
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
        verbose_name="Slug тега",
        help_text="Введите текстовый идентификатор тега",
        max_length=settings.MAX_LEGTH,
        unique=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name="Название интредиента",
        help_text="Введите название ингредиента",
        max_length=settings.MAX_LEGTH,
    )
    measurement_unit = models.CharField(
        verbose_name="Единицы измерения",
        max_length=settings.MAX_LEGTH,
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
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name="recipe",
        verbose_name="Автор публикации",
        help_text="Выберите автора рецепта",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Название рецепта",
        help_text="Введите название рецепта",
        max_length=settings.MAX_LEGTH,
    )
    image = models.ImageField(
        verbose_name="Изображение",
        help_text="Выберите изображение рецепта",
        upload_to="recipes/images",
    )
    text = models.TextField(
        verbose_name="Описание рецепта", help_text="Введите описания рецепта"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name="recipes",
        verbose_name="Ингредиенты для приготовления блюда по рецепту",
        help_text="Выберите ингредиенты рецепта",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тег",
        related_name="recipes",
        help_text="Выберите тег рецепта",
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления",
        help_text="Введите время приготовления",
        validators=(MinValueValidator(1, "Значение не может быть 0"),),
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации рецепта",
        help_text="Добавить дату создания",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)

    def __str__(self):
        return f"Автор: {self.author.username} рецепт: {self.name}"


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
        validators=(
            MinValueValidator(1, "Минимальное количество ингредиентов 1"),
        ),
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
        related_name="user_favorite",
        verbose_name="Автор списка избранного",
        help_text="Выберите автора",
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="recipe_favorite",
        verbose_name="Избранный рецепт",
        help_text="Выберите рецепт",
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique favourite"
            )
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        ordering = ("id",)

    def __str__(self):
        return (
            f"Пользователь: {self.user.username}" f"рецепт: {self.recipe.name}"
        )


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
    date_added = models.DateTimeField(
        verbose_name="Дата добавления", auto_now_add=True, editable=False
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
            f"Пользователь: {self.user.username},"
            f"рецепт в списке: {self.recipe.name}"
        )
