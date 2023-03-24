from django.conf import settings
from django.contrib.admin import ModelAdmin, TabularInline, register, site
from django.core.handlers.wsgi import WSGIRequest
from django.utils.safestring import SafeString, mark_safe
from recipes.models import (AmountIngredient, Carts, Favorites, Ingredient,
                            Recipe, Tag)

site.site_header = "Администрирование приложения Foodgram"

extra = settings.EXTRA


class IngredientInline(TabularInline):
    model = AmountIngredient
    extra = extra


@register(AmountIngredient)
class LinksAdmin(ModelAdmin):
    pass


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    search_fields = ("name",)
    list_filter = ("name",)

    save_on_top = True
    empty_value_display = "-пусто-"


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        "name",
        "author",
        "get_image",
        "count_favorites",
    )
    fields = (
        (
            "name",
            "cooking_time",
        ),
        (
            "author",
            "tags",
        ),
        ("text",),
        ("image",),
    )
    raw_id_fields = ("author",)
    search_fields = (
        "name",
        "author__username",
        "tags__name",
    )
    list_filter = ("name", "author__username", "tags__name")

    inlines = (IngredientInline,)
    save_on_top = True
    empty_value_display = "-пусто-"

    def get_image(self, obj: Recipe) -> SafeString:
        return mark_safe(f'<img src={obj.image.url} width="80" hieght="30"')

    get_image.short_description = "Изображение"

    def count_favorites(self, obj: Recipe) -> int:
        return obj.in_favorites.count()

    count_favorites.short_description = "В избранном"


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("id", "name", "slug", "color")
    list_display_links = ("id", "name")
    search_fields = ("name", "color")
    save_on_top = True
    empty_value_display = "-пусто-"


@register(Favorites)
class FavoriteAdmin(ModelAdmin):
    list_display = ("user", "recipe", "date_added")
    search_fields = ("user__username", "recipe__name")

    def has_change_permission(
        self, request: WSGIRequest, obj: Favorites or None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: WSGIRequest, obj: Favorites or None = None
    ) -> bool:
        return False


@register(Carts)
class CartAdmin(ModelAdmin):
    list_display = ("user", "recipe", "date_added")
    search_fields = ("user__username", "recipe__name")

    def has_change_permission(
        self, request: WSGIRequest, obj: Carts or None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: WSGIRequest, obj: Carts or None = None
    ) -> bool:
        return False
