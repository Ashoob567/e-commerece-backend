import django_filters
from django.db.models import Count, Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    min_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="lte")
    size = django_filters.CharFilter(field_name="variants__size")
    color = django_filters.CharFilter(field_name="variants__color")
    is_featured = django_filters.BooleanFilter()
    is_on_sale = django_filters.BooleanFilter(method="filter_on_sale")
    tags = django_filters.CharFilter(field_name="tags__slug")
    ordering = django_filters.OrderingFilter(
        choices=[
            ("price_asc", "Price: Low to High"),
            ("price_desc", "Price: High to Low"),
            ("newest", "Newest First"),
            ("most_popular", "Most Popular"),
        ],
        fields={
            "base_price": "price_asc",
            "-base_price": "price_desc",
            "created_at": "newest",
        },
    )

    class Meta:
        model = Product
        fields = []

    def filter_on_sale(self, queryset, name, value):
        if value:
            return queryset.filter(
                sale_price__isnull=False, sale_price__lt=django_filters.F("base_price")
            )
        return queryset.exclude(
            sale_price__isnull=False, sale_price__lt=django_filters.F("base_price")
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        if self.data.get("ordering") == "most_popular":
            queryset = queryset.annotate(
                total_sold=Count("order_items", distinct=True)
            ).order_by("-total_sold")

        return queryset
