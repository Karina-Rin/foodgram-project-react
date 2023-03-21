from django.conf import settings
from rest_framework.pagination import PageNumberPagination

page_size = settings.PAGE_SIZE


class PageLimitPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_size = page_size
