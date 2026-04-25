from math import ceil

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ProductPagination(PageNumberPagination):
    page_size = 12

    def get_paginated_response(self, data):
        return Response({
            "total_count": self.page.paginator.count,
            "total_pages": ceil(self.page.paginator.count / self.page_size),
            "current_page": self.page.number,
            "results": data,
        })
