from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    ProductListView,
    ProductDetailView,
    FeaturedProductsView,
    NewArrivalsView,
    BestsellersView,
    CategoryProductsView,
    ProductImageUploadView,
)

app_name = "products"

urlpatterns = [
    # Product endpoints
    path("", ProductListView.as_view(), name="product-list"),
    path("featured/", FeaturedProductsView.as_view(), name="featured-products"),
    path("new-arrivals/", NewArrivalsView.as_view(), name="new-arrivals"),
    path("bestsellers/", BestsellersView.as_view(), name="bestsellers"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("<uuid:pk>/images/", ProductImageUploadView.as_view(), name="product-image-upload"),

    # Category endpoints — registered under /api/products/ AND mirrored
    # via config/urls.py at /api/categories/ (see note below)
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"),
    path("categories/<slug:slug>/products/", CategoryProductsView.as_view(), name="category-products"),
]