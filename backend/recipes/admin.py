from django.contrib import admin
from django.utils.safestring import SafeString, mark_safe

from recipes.models import (Ingredient, IngredientAmount, Recipe,
                            RecipeFavorite, ShoppingCart, Subscribe, Tag)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientAmount
    fields = ("ingredient", "amount")
    min_num = 1
    extra = 0


class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "color", "slug")
    search_fields = ("name", "color", "slug")
    list_filter = ("name",)
    empty_value_display = "-пусто-"


class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    list_editable = (
        "name",
        "measurement_unit",
    )
    search_fields = ("name",)
    empty_value_display = "-пусто-"


class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "recipe",
        "ingredient",
        "amount",
    )
    list_editable = ("ingredient", "amount")
    search_fields = ("ingredient",)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "author", "count_favorites", "image")
    search_fields = ("name", "author", "tags")
    list_filter = ("author", "name", "tags")
    exclude = ("ingredients",)
    filter_vertical = ("tags",)
    inlines = (IngredientRecipeInline,)
    empty_value_display = "-пусто-"

    def get_image(self, obj: Recipe) -> SafeString:
        return mark_safe(f'<img src={obj.image.url} width="80" hieght="30"')

    get_image.short_description = "Изображение"

    def count_favorites(self, obj: Recipe) -> int:
        return obj.recipe.count()

    count_favorites.short_description = "В избранном"


class RecipeFavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    list_editable = (
        "user",
        "recipe",
    )
    list_filter = ("user",)
    empy_value_display = "-пусто-"


class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "author",
        "user",
    )
    list_editable = (
        "user",
        "author",
    )
    list_filter = ("user", "author")
    empy_value_display = "-пусто-"


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("recipe", "user")
    list_filter = ("recipe", "user")
    search_fields = ("user",)
    empty_value_display = "-пусто-"


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(RecipeFavorite, RecipeFavoriteAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
