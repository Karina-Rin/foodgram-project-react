from django.conf import settings
from django.contrib import admin
from recipes.models import (Ingredient, IngredientAmount, Recipe,
                            RecipeFavorite, ShoppingCart, Tag)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientAmount
    extra = 0


class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "id", "name", "color", "slug")
    search_fields = ("name", "slug")
    list_filter = (
        "name",
        "slug",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "id", "name", "measurement_unit")
    search_fields = ("name", "measurement_unit")
    list_filter = ("name",)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "count_favorites")
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    list_filter = (
        "author",
        "name",
        "tags",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY

    def count_favorites(self, obj):
        return obj.favorites.count()


class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ("pk", "id", "recipe", "ingredient", "amount")
    search_fields = (
        "recipe",
        "ingredient",
    )
    list_filter = (
        "recipe",
        "ingredient",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class RecipeFavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "id", "user", "recipe")
    search_fields = (
        "user",
        "recipe",
    )
    list_filter = (
        "user",
        "recipe",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("pk", "id", "user", "recipe")
    search_fields = (
        "user",
        "recipe",
    )
    list_filter = (
        "user",
        "recipe",
    )
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(RecipeFavorite, RecipeFavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
