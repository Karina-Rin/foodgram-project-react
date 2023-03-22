from django.contrib.admin import (ModelAdmin, TabularInline, display, register,
                                  site)
from django.core.handlers.wsgi import WSGIRequest
from django.forms import ModelForm
from django.forms.widgets import TextInput
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

from recipes.models import (AmountIngredient, Ingredient, Recipe,
                            RecipeFavorite, ShoppingCart, Tag)

site.site_header = "Администрирование приложения Foodgram"


class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = "__all__"
        widgets = {
            "color": TextInput(attrs={"type": "color"}),
        }


class IngredientInline(TabularInline):
    model = AmountIngredient
    extra = 2


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
    form = TagForm
    list_display = (
        "name",
        "slug",
        "color_code",
    )
    search_fields = ("name", "color")

    save_on_top = True
    empty_value_display = "-пусто-"

    @display(description="Colored")
    def color_code(self, obj: Tag):
        return format_html(
            '<span style="color: #{};">{}</span>', obj.color[1:], obj.color
        )

    color_code.short_description = "HEX-код цвета тэга"


@register(RecipeFavorite)
class RecipeFavoriteAdmin(ModelAdmin):
    list_display = ("user", "recipe", "date_added")
    search_fields = ("user__username", "recipe__name")

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@register(ShoppingCart)
class ShoppingCartdAdmin(ModelAdmin):
    list_display = ("user", "recipe", "date_added")
    search_fields = ("user__username", "recipe__name")

    def has_change_permission(
        self, request: WSGIRequest, obj: ShoppingCart or None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: WSGIRequest, obj: ShoppingCart or None = None
    ) -> bool:
        return False
