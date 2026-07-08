from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """Paginação padrão: ?page= e ?page_size= (10/25/50/100), com metadados completos."""
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "results": data,
            "count": self.page.paginator.count,
            "page": self.page.number,
            "pageSize": self.get_page_size(self.request),
            "totalPages": self.page.paginator.num_pages,
            # compat com consumidores DRF padrão
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
        })
