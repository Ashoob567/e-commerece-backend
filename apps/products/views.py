from django.db.models import Avg, Count, Sum
from django.db.models.functions import Coalesce

from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Category, Product
from .serializers import CategorySerializer, ProductDetailSerializer, ProductListSerializer
from .pagination import ProductPagination
from .filters import ProductFilter


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(
            parent__isnull=True, is_active=True
        ).prefetch_related("children")


class CategoryDetailView(RetrieveAPIView):
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Category.objects.filter(is_active=True)


class ProductListView(ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination
    filterset_class = ProductFilter

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images", "variants", "tags")
            .annotate(
                average_rating=Avg("reviews__rating"),
                review_count=Coalesce(Count("reviews"), 0),
            )
        )


class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .prefetch_related("images", "variants", "tags")
            .annotate(
                average_rating=Avg("reviews__rating"),
                review_count=Coalesce(Count("reviews"), 0),
            )
        )


class FeaturedProductsView(ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, is_featured=True)
            .select_related("category")
            .prefetch_related("images", "variants", "tags")
            .annotate(
                average_rating=Avg("reviews__rating"),
                review_count=Coalesce(Count("reviews"), 0),
            )[:8]
        )


class NewArrivalsView(ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images", "variants", "tags")
            .annotate(
                average_rating=Avg("reviews__rating"),
                review_count=Coalesce(Count("reviews"), 0),
            )
            .order_by("-created_at")[:8]
        )


class BestsellersView(ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images", "variants", "tags")
            .annotate(
                average_rating=Avg("reviews__rating"),
                review_count=Coalesce(Count("reviews"), 0),
            )
            .order_by("-review_count")[:8]
        )


class CategoryProductsView(ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        category_slug = self.kwargs.get("slug")
        return (
            Product.objects.filter(
                is_active=True, category__slug=category_slug
            )
            .select_related("category")
            .prefetch_related("images", "variants", "tags")
            .annotate(
                average_rating=Avg("reviews__rating"),
                review_count=Coalesce(Count("reviews"), 0),
            )
        )