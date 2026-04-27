import logging

from django.db.models import Avg, Count, Sum
from django.db.models.functions import Coalesce
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAdminUser

from .models import Category, Product, ProductImage
from .serializers import CategorySerializer, ProductDetailSerializer, ProductListSerializer
from .pagination import ProductPagination
from .filters import ProductFilter
from utils.storage import SupabaseStorage

logger = logging.getLogger(__name__)


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


class ProductImageUploadView(APIView):
    """
    Upload product images to Supabase Storage.

    POST /api/products/<id>/images/
    Admin only. Accepts multipart/form-data with up to 8 image files.

    Validation:
    - Max file size: 5MB per image
    - Allowed formats: jpg, jpeg, png, webp
    - Max files: 8 per request
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    ALLOWED_FORMATS = ["jpg", "jpeg", "png", "webp"]
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_FILES = 8

    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        files = request.FILES.getlist("images")

        if not files:
            return Response(
                {"error": "No images provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(files) > self.MAX_FILES:
            return Response(
                {"error": f"Maximum {self.MAX_FILES} images allowed per request"},
                status=status.HTTP_400_BAD_REQUEST
            )

        storage = SupabaseStorage()
        uploaded_images = []
        errors = []

        for file in files:
            try:
                # Validate file size
                if file.size > self.MAX_FILE_SIZE:
                    errors.append({
                        "file": file.name,
                        "error": f"File size exceeds 5MB limit ({file.size} bytes)"
                    })
                    continue

                # Validate file format
                file_ext = file.name.split(".")[-1].lower() if "." in file.name else ""
                content_type = file.content_type.lower() if file.content_type else ""

                is_valid_format = (
                    file_ext in self.ALLOWED_FORMATS or
                    content_type in [f"image/{ext}" for ext in self.ALLOWED_FORMATS]
                )

                if not is_valid_format:
                    errors.append({
                        "file": file.name,
                        "error": f"Invalid format. Allowed: {', '.join(self.ALLOWED_FORMATS)}"
                    })
                    continue

                # Generate unique filename
                import uuid
                unique_name = f"{uuid.uuid4().hex}.{file_ext or 'jpg'}"

                # Upload to Supabase
                storage.save(unique_name, file)

                # Get public URL
                public_url = storage.url(unique_name)

                # Create ProductImage instance
                product_image = ProductImage.objects.create(
                    product=product,
                    image_url=public_url,
                    alt_text="",
                    is_primary=product.images.count() == 0,  # First image is primary
                    order=product.images.count()
                )

                uploaded_images.append({
                    "id": str(product_image.id),
                    "url": public_url,
                    "is_primary": product_image.is_primary
                })

                logger.info(f"Uploaded image for product {product.name}: {public_url}")

            except Exception as e:
                logger.error(f"Error uploading image {file.name}: {e}")
                errors.append({
                    "file": file.name,
                    "error": str(e)
                })

        response_data = {
            "uploaded": uploaded_images,
            "product_id": str(product.id)
        }

        if errors:
            response_data["errors"] = errors

        return Response(response_data, status=status.HTTP_201_CREATED)