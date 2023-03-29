from recipes.models import Recipe
from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        author_id = self.request.query_params.get("author_id", None)
        if author_id:
            author_recipe_count = Recipe.objects.filter(
                author_id=author_id
            ).count()
            if author_recipe_count > self.page_size:
                remaining_count = author_recipe_count - self.page_size
                text = f"Ещё {remaining_count} рецептов..."
                response.data["next"] = text
        return response
