from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import (CASCADE, PROTECT, SET_NULL, CheckConstraint,
                              DateTimeField, Q, UniqueConstraint)
from PIL import Image

from api.validators import hex_color_validator

max_legth = settings.MAX_LEGTH
min_cook_time = settings.MIN_COOK_TIME
max_cook_time = settings.MAX_COOK_TIME
recipe_umage_size = settings.RECIPE_IMAGE_SIZE
min_amount_imgr = settings.MIN_AMOUNT_INGR
max_amount_imgr = settings.MAX_AMOUNT_INGR

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name="Название",
        max_length=max_legth,
        help_text="Введите название тэга",
        unique=True,
    )
    color = models.CharField(
        verbose_name="HEX-код",
        help_text="Введите HEX-код цвета тэга",
        max_length=7,
        default="#FF0000",
        unique=True,
        null=True,
        db_index=False,
    )
    slug = models.CharField(
        verbose_name="Слаг тэга",
        help_text="Введите текстовый идентификатор тэга",
        max_length=max_legth,
        unique=True,
        db_index=False,
    )

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("name",)

    def __str__(self) -> str:
        return "{} (color: {})".format(self.name, self.color)

    def clean_fields(self, *args, **kwargs) -> None:
        self.name = self.name.strip().lower()
        self.slug = self.slug.strip().lower()
        self.color = hex_color_validator(self.color)
        super().clean_fields(*args, **kwargs)


class Ingredient(models.Model):
    name = models.TextField(
        verbose_name="Название ингредиента",
        help_text="Введите название ингредиента",
        max_length=max_legth,
        validators=[MinLengthValidator(1)],
    )
    measurement_unit = models.TextField(
        verbose_name="Единицы измерения",
        max_length=max_legth,
        help_text="Введите единицы измерения",
        validators=[MinLengthValidator(1)],
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)
        constraints = (
            UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_for_ingredient",
            ),
            CheckConstraint(
                check=Q(name__length__gt=0),
                name="\n%(app_label)s_%(class)s_name пусто\n",
            ),
            CheckConstraint(
                check=Q(measurement_unit__length__gt=0),
                name="\n%(app_label)s_%(class)s_measurement_unit пусто\n",
            ),
        )

    def __str__(self) -> str:
        return f"{self.name} {self.measurement_unit}"

    def clean(self) -> None:
        self.name = self.name.lower()
        self.measurement_unit = self.measurement_unit.lower()
        super().clean()


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name="Автор рецепта",
        related_name="recipes",
        help_text="Выберите автора рецепта",
        on_delete=SET_NULL,
        null=True,
    )
    name = models.CharField(
        verbose_name="Название рецепта",
        help_text="Введите название рецепта",
        max_length=max_legth,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты для приготовления блюда по рецепту",
        related_name="recipes",
        help_text="Выберите ингредиенты рецепта",
        through="recipes.AmountIngredient",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тэг",
        related_name="recipes",
        help_text="Выберите тэг рецепта.",
    )
    image = models.ImageField(
        verbose_name="Изображение",
        help_text="Выберите изображение рецепта",
        upload_to="recipe_images/",
    )
    text = models.TextField(
        verbose_name="Описание рецепта",
        help_text="Введите описание рецепта",
        max_length=max_legth,
        db_index=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления",
        help_text="Введите время приготовления",
        default=0,
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)
        constraints = (
            UniqueConstraint(
                fields=("name", "author"),
                name="unique_for_author",
            ),
            CheckConstraint(
                check=Q(name__length__gt=0),
                name="\n%(app_label)s_%(class)s_name пусто\n",
            ),
        )

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        self.name = self.name.capitalize()
        super().clean()

    def resize_and_save_image(self):
        if self.image:
            image = Image.open(self.image.path)
            image = image.resize(recipe_umage_size)
            image.save(self.image.path)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self


class AmountIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        related_name="ingredient",
        help_text="Выберите рецепт",
        on_delete=CASCADE,
    )
    ingredients = models.ForeignKey(
        Ingredient,
        verbose_name="Ингредиент",
        related_name="recipe",
        help_text="Добавить ингредиенты рецепта в корзину",
        on_delete=PROTECT,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        help_text="Введите количество ингредиентов",
        default=0,
    )

    class Meta:
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        ordering = ("recipe",)
        constraints = (
            UniqueConstraint(
                fields=(
                    "recipe",
                    "ingredients",
                ),
                name="\n%(app_label)s_%(class)s ингредиент уже добавлен\n",
            ),
        )

    def __str__(self) -> str:
        return f"{self.amount} {self.ingredients}"


class RecipeFavorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Автор списка избранного",
        related_name="favorites",
        help_text="Выберите автора",
        on_delete=CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Избранный рецепт",
        related_name="in_favorites",
        help_text="Выберите рецепт",
        on_delete=CASCADE,
    )
    date_added = DateTimeField(
        verbose_name="Дата добавления", auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = (
            UniqueConstraint(
                fields=(
                    "recipe",
                    "user",
                ),
                name="Рецепт уже в избранном",
            ),
        )

    def __str__(self) -> str:
        return f"{self.user} -> {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Автор списка покупок",
        related_name="shopping_cart",
        help_text="Выберите автора",
        on_delete=CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепты в списке покупок",
        related_name="in_shopping_carts",
        help_text="Выберите рецепты для добавления продуктов в корзину",
        on_delete=CASCADE,
    )
    date_added = models.DateTimeField(
        verbose_name="Дата добавления", auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = "Рецепт в списке покупок"
        verbose_name_plural = "Рецепты в списке покупок"
        constraints = (
            UniqueConstraint(
                fields=(
                    "recipe",
                    "user",
                ),
                name="\n%(app_label)s_%(class)s рецепт уже есть в корзине\n",
            ),
        )

    def __str__(self) -> str:
        return f"{self.user} -> {self.recipe}"
