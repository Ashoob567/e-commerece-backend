"""
Comprehensive product API tests for Luxe Market.
Tests for product list, filters, detail, featured, arrivals, and image upload.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.products.models import Category, Product, ProductVariant, ProductImage, ProductTag, Review
from apps.products.filters import ProductFilter

User = get_user_model()


def make_category(name="Electronics", slug="electronics", parent=None, is_active=True):
    return Category.objects.create(
        name=name, slug=slug, is_active=is_active, parent=parent
    )


def make_product(name="Test Product", slug="test-product", category=None,
                 base_price=Decimal("99.99"), sale_price=None,
                 is_featured=False, is_active=True, description="Test description"):
    return Product.objects.create(
        name=name,
        slug=slug,
        description=description,
        category=category,
        base_price=base_price,
        sale_price=sale_price,
        is_featured=is_featured,
        is_active=is_active,
    )


def make_variant(product, sku="SKU-001", size="M", color="Black", stock_qty=10, price_modifier=Decimal("0")):
    return ProductVariant.objects.create(
        product=product,
        sku=sku,
        size=size,
        color=color,
        stock_qty=stock_qty,
        price_modifier=price_modifier,
    )


def make_image(product, image_url="https://example.com/image.jpg", is_primary=False, order=0):
    return ProductImage.objects.create(
        product=product,
        image_url=image_url,
        is_primary=is_primary,
        order=order,
    )


class ProductListAPITests(TestCase):
    """Tests for product listing and pagination."""

    def setUp(self):
        self.client = APIClient()
        self.category = make_category()
        for i in range(25):
            make_product(
                name=f"Product {i}",
                slug=f"product-{i}",
                category=self.category,
                base_price=Decimal(f"{(i + 1) * 10}.00"),
            )

    def test_list_products_returns_paginated_response(self):
        """List products returns paginated response with correct shape."""
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Check pagination fields
        self.assertIn("count", data)
        self.assertIn("next", data)
        self.assertIn("previous", data)
        self.assertIn("results", data)
        # Check results is a list
        self.assertIsInstance(data["results"], list)
        # Check each product has required fields
        for product in data["results"]:
            self.assertIn("id", product)
            self.assertIn("name", product)
            self.assertIn("slug", product)
            self.assertIn("base_price", product)

    def test_list_products_pagination_size(self):
        """Pagination returns correct page size (20 per page)."""
        response = self.client.get("/api/products/")
        data = response.json()
        self.assertEqual(len(data["results"]), 20)
        self.assertIsNotNone(data["next"])  # Should have next page

    def test_list_products_second_page(self):
        """Second page returns remaining products."""
        response = self.client.get("/api/products/?page=2")
        data = response.json()
        self.assertEqual(len(data["results"]), 5)  # Remaining 5 products
        self.assertIsNone(data["next"])  # No more pages


class ProductFilterAPITests(TestCase):
    """Tests for product filtering."""

    def setUp(self):
        self.client = APIClient()
        self.electronics = make_category(name="Electronics", slug="electronics")
        self.fashion = make_category(name="Fashion", slug="fashion")

        # Create products with different categories and prices
        self.cheap_electronic = make_product(
            name="Cheap Electronic", slug="cheap-electronic",
            category=self.electronics, base_price=Decimal("10.00")
        )
        self.expensive_electronic = make_product(
            name="Expensive Electronic", slug="expensive-electronic",
            category=self.electronics, base_price=Decimal("500.00")
        )
        self.cheap_fashion = make_product(
            name="Cheap Fashion", slug="cheap-fashion",
            category=self.fashion, base_price=Decimal("20.00")
        )
        self.expensive_fashion = make_product(
            name="Expensive Fashion", slug="expensive-fashion",
            category=self.fashion, base_price=Decimal("300.00")
        )

    def test_filter_by_category_slug(self):
        """Filter products by category slug works correctly."""
        response = self.client.get("/api/products/?category=electronics")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        slugs = {p["slug"] for p in data["results"]}
        self.assertIn("cheap-electronic", slugs)
        self.assertIn("expensive-electronic", slugs)
        self.assertNotIn("cheap-fashion", slugs)
        self.assertNotIn("expensive-fashion", slugs)

    def test_filter_by_min_price(self):
        """Filter products by minimum price."""
        response = self.client.get("/api/products/?min_price=100")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        for product in data["results"]:
            self.assertGreaterEqual(Decimal(product["base_price"]), Decimal("100"))

    def test_filter_by_max_price(self):
        """Filter products by maximum price."""
        response = self.client.get("/api/products/?max_price=50")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        for product in data["results"]:
            self.assertLessEqual(Decimal(product["base_price"]), Decimal("50"))

    def test_filter_by_price_range(self):
        """Filter by price range (min_price, max_price) works correctly."""
        response = self.client.get("/api/products/?min_price=15&max_price=350")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        slugs = {p["slug"] for p in data["results"]}
        # Should include: expensive-fashion (300), cheap-fashion (20)
        self.assertIn("expensive-fashion", slugs)
        self.assertIn("cheap-fashion", slugs)
        # Should exclude: cheap-electronic (10), expensive-electronic (500)
        self.assertNotIn("cheap-electronic", slugs)
        self.assertNotIn("expensive-electronic", slugs)


class ProductDetailAPITests(TestCase):
    """Tests for product detail endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.category = make_category()
        self.product = make_product(
            name="Detailed Product",
            slug="detailed-product",
            category=self.category,
            base_price=Decimal("199.99"),
        )
        # Add variants
        self.variant1 = make_variant(self.product, sku="VAR-001", size="S", color="Red")
        self.variant2 = make_variant(self.product, sku="VAR-002", size="M", color="Blue")
        # Add images
        self.image1 = make_image(self.product, image_url="https://example.com/img1.jpg", is_primary=True, order=0)
        self.image2 = make_image(self.product, image_url="https://example.com/img2.jpg", is_primary=False, order=1)
        # Add tags
        self.tag = ProductTag.objects.create(name="Premium", slug="premium")
        self.product.tags.add(self.tag)

    def test_product_detail_returns_all_data(self):
        """Get product detail by slug returns all variants and images."""
        response = self.client.get("/api/products/detailed-product/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Check basic fields
        self.assertEqual(data["slug"], "detailed-product")
        self.assertEqual(data["name"], "Detailed Product")
        # Check images
        self.assertIn("images", data)
        self.assertEqual(len(data["images"]), 2)
        self.assertEqual(data["images"][0]["url"], "https://example.com/img1.jpg")
        self.assertTrue(data["images"][0]["is_primary"])
        # Check variants
        self.assertIn("variants", data)
        self.assertEqual(len(data["variants"]), 2)
        variant_skus = {v["sku"] for v in data["variants"]}
        self.assertIn("VAR-001", variant_skus)
        self.assertIn("VAR-002", variant_skus)
        # Check tags
        self.assertIn("tags", data)
        self.assertIn("premium", data["tags"])


class FeaturedProductsAPITests(TestCase):
    """Tests for featured products endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.category = make_category()
        # Create featured products
        for i in range(5):
            make_product(
                name=f"Featured {i}",
                slug=f"featured-{i}",
                category=self.category,
                is_featured=True,
                base_price=Decimal("100.00"),
            )
        # Create non-featured products
        for i in range(5):
            make_product(
                name=f"Regular {i}",
                slug=f"regular-{i}",
                category=self.category,
                is_featured=False,
                base_price=Decimal("50.00"),
            )

    def test_featured_products_returns_only_featured(self):
        """Featured products endpoint returns only featured=True items."""
        response = self.client.get("/api/products/featured/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertLessEqual(len(data), 8)  # Max 8 items
        for product in data:
            self.assertTrue(product["is_featured"])
        slugs = {p["slug"] for p in data}
        # Should only have featured products
        for i in range(5):
            self.assertIn(f"featured-{i}", slugs)
        # Should not have regular products
        for i in range(5):
            self.assertNotIn(f"regular-{i}", slugs)


class NewArrivalsAPITests(TestCase):
    """Tests for new arrivals endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.category = make_category()
        # Create products at different times (created_at auto-set)
        self.product1 = make_product(name="Newest", slug="newest", category=self.category)
        self.product2 = make_product(name="Older", slug="older", category=self.category)

    def test_new_arrivals_ordered_by_created_at_desc(self):
        """New arrivals returns products ordered by created_at desc."""
        response = self.client.get("/api/products/new-arrivals/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertLessEqual(len(data), 8)
        # Verify ordering (newest first)
        created_ats = [p["created_at"] for p in data]
        self.assertEqual(created_ats, sorted(created_ats, reverse=True))


class UnauthenticatedAccessAPITests(TestCase):
    """Tests that unauthenticated users can access read endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.category = make_category()
        self.product = make_product(category=self.category)

    def test_unauthenticated_can_access_product_list(self):
        """Unauthenticated user can access product list."""
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_can_access_product_detail(self):
        """Unauthenticated user can access product detail."""
        response = self.client.get(f"/api/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_can_access_featured(self):
        """Unauthenticated user can access featured products."""
        response = self.client.get("/api/products/featured/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_can_access_new_arrivals(self):
        """Unauthenticated user can access new arrivals."""
        response = self.client.get("/api/products/new-arrivals/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_can_access_categories(self):
        """Unauthenticated user can access categories."""
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProductImageUploadAPITests(TestCase):
    """Tests for product image upload endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.category = make_category()
        self.product = make_product(category=self.category)
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email="admin@luxemarket.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
        )
        # Login and get token
        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "admin@luxemarket.com", "password": "adminpass123"},
        )
        self.admin_token = login_response.data["access"]
        # Create regular user
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="userpass123",
            first_name="Regular",
            last_name="User",
        )
        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "user@example.com", "password": "userpass123"},
        )
        self.regular_token = login_response.data["access"]

    @patch("apps.products.views.SupabaseStorage")
    def test_upload_image_without_admin_token_returns_403(self, mock_storage_class):
        """Image upload without admin token returns 403."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.regular_token}")
        # Mock file upload
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        image_file = SimpleUploadedFile("test.jpg", b"fake image content", content_type="image/jpeg")
        response = self.client.post(
            f"/api/products/{self.product.id}/images/",
            {"images": image_file},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.products.views.SupabaseStorage")
    def test_upload_image_with_admin_token(self, mock_storage_class):
        """Image upload with admin token succeeds."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        # Mock storage
        mock_storage = MagicMock()
        mock_storage.save.return_value = "products/images/test.jpg"
        mock_storage.url.return_value = "https://example.com/products/images/test.jpg"
        mock_storage_class.return_value = mock_storage

        from django.core.files.uploadedfile import SimpleUploadedFile
        image_file = SimpleUploadedFile("test.jpg", b"fake image content", content_type="image/jpeg")
        response = self.client.post(
            f"/api/products/{self.product.id}/images/",
            {"images": image_file},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("uploaded", response.data)
        self.assertEqual(len(response.data["uploaded"]), 1)

    @patch("apps.products.views.SupabaseStorage")
    def test_upload_image_with_invalid_file_type(self, mock_storage_class):
        """Image upload with invalid file type returns 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

        from django.core.files.uploadedfile import SimpleUploadedFile
        # Invalid file type (PDF instead of image)
        invalid_file = SimpleUploadedFile("test.pdf", b"fake pdf content", content_type="application/pdf")
        response = self.client.post(
            f"/api/products/{self.product.id}/images/",
            {"images": invalid_file},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    @patch("apps.products.views.SupabaseStorage")
    def test_upload_multiple_images(self, mock_storage_class):
        """Upload multiple images in one request (up to 8)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        mock_storage = MagicMock()
        mock_storage.save.return_value = "products/images/test.jpg"
        mock_storage.url.return_value = "https://example.com/products/images/test.jpg"
        mock_storage_class.return_value = mock_storage

        from django.core.files.uploadedfile import SimpleUploadedFile
        images = [
            SimpleUploadedFile(f"test{i}.jpg", b"fake image content", content_type="image/jpeg")
            for i in range(5)
        ]
        response = self.client.post(
            f"/api/products/{self.product.id}/images/",
            {"images": images},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["uploaded"]), 5)

    @patch("apps.products.views.SupabaseStorage")
    def test_upload_too_many_images(self, mock_storage_class):
        """Upload more than 8 images returns 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

        from django.core.files.uploadedfile import SimpleUploadedFile
        images = [
            SimpleUploadedFile(f"test{i}.jpg", b"fake image content", content_type="image/jpeg")
            for i in range(10)
        ]
        response = self.client.post(
            f"/api/products/{self.product.id}/images/",
            {"images": images},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Maximum", response.data["error"])

    def test_upload_to_nonexistent_product(self):
        """Upload to non-existent product returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        from django.core.files.uploadedfile import SimpleUploadedFile
        image_file = SimpleUploadedFile("test.jpg", b"fake image content", content_type="image/jpeg")
        response = self.client.post(
            "/api/products/00000000-0000-0000-0000-000000000000/images/",
            {"images": image_file},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryProductsAPITests(TestCase):
    """Tests for category products endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.electronics = make_category(name="Electronics", slug="electronics")
        self.fashion = make_category(name="Fashion", slug="fashion")
        # Create products in electronics category
        make_product(name="Laptop", slug="laptop", category=self.electronics)
        make_product(name="Phone", slug="phone", category=self.electronics)
        # Create products in fashion category
        make_product(name="Shirt", slug="shirt", category=self.fashion)
        make_product(name="Pants", slug="pants", category=self.fashion)

    def test_category_products_filters_correctly(self):
        """Category products endpoint returns only products in that category."""
        response = self.client.get("/api/categories/electronics/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get("results", data)
        slugs = {p["slug"] for p in results}
        self.assertIn("laptop", slugs)
        self.assertIn("phone", slugs)
        self.assertNotIn("shirt", slugs)
        self.assertNotIn("pants", slugs)


class ProductFilterUnitTests(TestCase):
    """Unit tests for ProductFilter class."""

    def test_filter_by_category(self):
        """ProductFilter filters by category slug."""
        category = make_category(slug="test-cat")
        product = make_product(category=category)
        make_product(name="Other", slug="other", category=None)  # No category

        filterset = ProductFilter(data={"category": "test-cat"}, queryset=Product.objects.all())
        self.assertEqual(filterset.qs.count(), 1)
        self.assertIn(product, filterset.qs)

    def test_filter_by_price_range(self):
        """ProductFilter filters by price range."""
        make_product(name="Cheap", slug="cheap", base_price=Decimal("10.00"))
        make_product(name="Mid", slug="mid", base_price=Decimal("50.00"))
        make_product(name="Expensive", slug="expensive", base_price=Decimal("100.00"))

        filterset = ProductFilter(
            data={"min_price": "20", "max_price": "80"},
            queryset=Product.objects.all()
        )
        self.assertEqual(filterset.qs.count(), 1)
        self.assertEqual(filterset.qs.first().base_price, Decimal("50.00"))
