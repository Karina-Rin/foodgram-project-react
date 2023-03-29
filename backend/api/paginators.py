from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.response import Response


class PageLimitPagination(PageNumberPagination):
    page_size_query_param = "limit"


class RecipePagination(LimitOffsetPagination):
    default_limit = 3
    max_limit = 10

    def get_paginated_response(self, data):
        remaining_recipes = self.count - (self.offset + self.limit)
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "remaining_recipes": remaining_recipes,
                "results": data,
            }
        )
