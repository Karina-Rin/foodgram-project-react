from django.core import paginator
from rest_framework.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "limit"
    django_paginator_class = paginator.Paginator
    page_query_param = "page"
