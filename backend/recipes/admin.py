from django.contrib import admin
from django.utils.safestring import SafeString, mark_safe

from recipes.models import (Ingredient, IngredientAmount, Recipe,
                            RecipeFavorite, ShoppingCart, Subscribe, Tag)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientAmount
    extra = 0


class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "color", "slug")
    search_fields = ("name", "color", "slug")
    list_filter = ("name",)
    empty_value_display = "-пусто-"


class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("name", "slug")
    empty_value_display = "-пусто-"


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    autocomplete_fields = ("ingredient",)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "count_favorites", "image")
    search_fields = ("name", "author", "tags")
    list_filter = ("author", "name", "tags")
    exclude = ("ingredients",)
    filter_vertical = ("tags",)
    inlines = (IngredientAmountInline,)
    empty_value_display = "-пусто-"

    def get_image(self, obj: Recipe) -> SafeString:
        return mark_safe(f'<img src={obj.image.url} width="80" hieght="30"')

    get_image.short_description = "Изображение"

    def count_favorites(self, obj: Recipe) -> int:
        return obj.in_favorites.count()

    count_favorites.short_description = "В избранном"


class RecipeFavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "favorite_recipe")
    search_fields = "favorite_recipe"
    list_filter = ("id", "user", "favorite_recipe")
    empy_value_display = "-пусто-"


class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ("id", "recipe", "ingredient", "amount")
    search_fields = ("recipe", "ingredient")


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user", "recipe")
    list_filter = ("user", "recipe")
    empty_value_display = "-пусто-"


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "user", "created")
    search_fields = ("author", "created")
    list_filter = ("author", "user", "created")
    empy_value_display = "-пусто-"


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(RecipeFavorite, RecipeFavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
