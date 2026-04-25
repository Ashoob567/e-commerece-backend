from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.products.models import Category, Product, ProductVariant, ProductImage, ProductTag, Review

User = get_user_model()


def make_category(name="Electronics", slug="electronics", parent=None):
    return Category.objects.create(
        name=name, slug=slug, is_active=True, parent=parent
    )


def make_product(name="Test Product", slug="test-product", category=None,
                 base_price=Decimal("99.99"), is_featured=False, is_active=True):
    return Product.objects.create(
        name=name,
        slug=slug,
        description="Test description",
        category=category,
        base_price=base_price,
        is_featured=is_featured,
        is_active=is_active,
    )


class ProductAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.category = make_category()
        self.product = make_product(category=self.category)

    # ------------------------------------------------------------------ #
    # 1. Product Listing
    # ------------------------------------------------------------------ #
    def test_product_listing(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for key in ("total_count", "total_pages", "current_page", "results"):
            self.assertIn(key, data, msg=f"Missing key: {key}")

    # ------------------------------------------------------------------ #
    # 2. Filter by Category
    # ------------------------------------------------------------------ #
    def test_filter_by_category(self):
        cat = make_category(name="Fashion", slug="fashion")
        p1 = make_product(name="Shirt", slug="shirt", category=cat)
        p2 = make_product(name="Pants", slug="pants", category=cat)
        make_product(name="Laptop", slug="laptop", category=self.category)

        response = self.client.get(f"/api/products/?category_slug={cat.slug}")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        returned_slugs = {p["slug"] for p in results}
        self.assertIn("shirt", returned_slugs)
        self.assertIn("pants", returned_slugs)
        self.assertNotIn("laptop", returned_slugs)

    # ------------------------------------------------------------------ #
    # 3. Filter by Price Range
    # ------------------------------------------------------------------ #
    def test_filter_by_price_range(self):
        make_product(name="Cheap", slug="cheap", base_price=Decimal("10.00"))
        make_product(name="Mid", slug="mid", base_price=Decimal("50.00"))
        make_product(name="Expensive", slug="expensive", base_price=Decimal("200.00"))

        response = self.client.get("/api/products/?min_price=20&max_price=100")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        returned_slugs = {p["slug"] for p in results}
        self.assertIn("mid", returned_slugs)
        self.assertNotIn("cheap", returned_slugs)
        self.assertNotIn("expensive", returned_slugs)

    # ------------------------------------------------------------------ #
    # 4. Product Detail
    # ------------------------------------------------------------------ #
    def test_product_detail(self):
        response = self.client.get(f"/api/products/{self.product.slug}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for key in ("images", "variants", "tags", "average_rating", "review_count"):
            self.assertIn(key, data, msg=f"Missing key: {key}")

    # ------------------------------------------------------------------ #
    # 5. Featured Products
    # ------------------------------------------------------------------ #
    def test_featured_products(self):
        for i in range(10):
            make_product(
                name=f"Featured {i}",
                slug=f"featured-{i}",
                is_featured=True,
                category=self.category,
            )

        response = self.client.get("/api/products/featured/")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertLessEqual(len(results), 8)
        self.assertTrue(all(p["is_featured"] for p in results))

    # ------------------------------------------------------------------ #
    # 6. New Arrivals
    # ------------------------------------------------------------------ #
    def test_new_arrivals(self):
        for i in range(10):
            make_product(
                name=f"New {i}",
                slug=f"new-{i}",
                category=self.category,
            )

        response = self.client.get("/api/products/new-arrivals/")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertLessEqual(len(results), 8)

        created_ats = [p["created_at"] for p in results]
        self.assertEqual(created_ats, sorted(created_ats, reverse=True))

    # ------------------------------------------------------------------ #
    # 7. Category Listing
    # ------------------------------------------------------------------ #
    def test_category_listing(self):
        child = make_category(name="Laptops", slug="laptops", parent=self.category)

        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) > 0)

        top_level = [c for c in data if c["slug"] == self.category.slug]
        self.assertEqual(len(top_level), 1)
        self.assertIn("children", top_level[0])
        children_slugs = [ch["slug"] for ch in top_level[0]["children"]]
        self.assertIn("laptops", children_slugs)

    # ------------------------------------------------------------------ #
    # 8. Category Products
    # ------------------------------------------------------------------ #
    def test_category_products(self):
        cat = make_category(name="Books", slug="books")
        make_product(name="Novel", slug="novel", category=cat)
        make_product(name="Textbook", slug="textbook", category=cat)
        make_product(name="Phone", slug="phone", category=self.category)

        response = self.client.get(f"/api/categories/{cat.slug}/products/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data["results"] if "results" in data else data
        returned_slugs = {p["slug"] for p in results}
        self.assertIn("novel", returned_slugs)
        self.assertIn("textbook", returned_slugs)
        self.assertNotIn("phone", returned_slugs)