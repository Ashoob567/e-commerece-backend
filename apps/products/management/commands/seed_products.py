from django.core.management.base import BaseCommand
from django.db import transaction

from apps.products.models import Category, Product, ProductTag, ProductVariant


class Command(BaseCommand):
    help = "Seed the database with initial product data (idempotent)"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting product seed..."))

        # Create tags
        self.stdout.write("Creating product tags...")
        new_arrival, _ = ProductTag.objects.get_or_create(
            name="New Arrival", defaults={"slug": "new-arrival"}
        )
        best_seller, _ = ProductTag.objects.get_or_create(
            name="Best Seller", defaults={"slug": "best-seller"}
        )

        # Create categories
        self.stdout.write("Creating categories...")
        watches_category, _ = Category.objects.get_or_create(name="Watches")
        undergarments_category, _ = Category.objects.get_or_create(name="Undergarments")

        # Create Watches products
        self.stdout.write("Creating watches products...")
        watches_data = [
            {
                "name": "Classic Gold Watch",
                "base_price": "299.99",
                "sale_price": "249.99",
                "variants": [
                    {"size": None, "color": "Brown", "sku": "WATCH-001-BRN"},
                    {"size": None, "color": "Black", "sku": "WATCH-001-BLK"},
                ],
                "tags": [new_arrival],
            },
            {
                "name": "Slim Silver Watch",
                "base_price": "199.99",
                "sale_price": None,
                "variants": [
                    {"size": None, "color": "Silver", "sku": "WATCH-002-SLV"},
                    {"size": None, "color": "Gold", "sku": "WATCH-002-GLD"},
                ],
                "tags": [best_seller],
            },
            {
                "name": "Sport Black Watch",
                "base_price": "349.99",
                "sale_price": "299.99",
                "variants": [
                    {"size": None, "color": "Black", "sku": "WATCH-003-BLK"},
                    {"size": None, "color": "Navy", "sku": "WATCH-003-NVY"},
                ],
                "tags": [new_arrival, best_seller],
            },
        ]

        for watch_data in watches_data:
            product, created = Product.objects.get_or_create(
                name=watch_data["name"],
                defaults={
                    "category": watches_category,
                    "description": f"Elegant {watch_data['name']} for the modern individual.",
                    "base_price": watch_data["base_price"],
                    "sale_price": watch_data["sale_price"],
                },
            )
            if created:
                product.tags.set(watch_data["tags"])
                for variant_data in watch_data["variants"]:
                    ProductVariant.objects.create(
                        product=product,
                        size=variant_data["size"],
                        color=variant_data["color"],
                        sku=variant_data["sku"],
                        stock_qty=50,
                    )
                self.stdout.write(f"  Created: {watch_data['name']}")

        # Create Undergarments products
        self.stdout.write("Creating undergarments products...")
        undergarments_data = [
            {
                "name": "Silk Bralette",
                "base_price": "49.99",
                "sale_price": "39.99",
                "variants": [
                    {"size": "S", "color": None, "sku": "UND-001-S"},
                    {"size": "M", "color": None, "sku": "UND-001-M"},
                    {"size": "L", "color": None, "sku": "UND-001-L"},
                ],
                "tags": [new_arrival],
            },
            {
                "name": "Cotton Brief Set",
                "base_price": "29.99",
                "sale_price": None,
                "variants": [
                    {"size": "S", "color": None, "sku": "UND-002-S"},
                    {"size": "M", "color": None, "sku": "UND-002-M"},
                    {"size": "L", "color": None, "sku": "UND-002-L"},
                ],
                "tags": [best_seller],
            },
            {
                "name": "Lace Bodysuit",
                "base_price": "79.99",
                "sale_price": "59.99",
                "variants": [
                    {"size": "S", "color": None, "sku": "UND-003-S"},
                    {"size": "M", "color": None, "sku": "UND-003-M"},
                    {"size": "L", "color": None, "sku": "UND-003-L"},
                ],
                "tags": [new_arrival, best_seller],
            },
        ]

        for underwear_data in undergarments_data:
            product, created = Product.objects.get_or_create(
                name=underwear_data["name"],
                defaults={
                    "category": undergarments_category,
                    "description": f"Comfortable and stylish {underwear_data['name']}.",
                    "base_price": underwear_data["base_price"],
                    "sale_price": underwear_data["sale_price"],
                },
            )
            if created:
                product.tags.set(underwear_data["tags"])
                for variant_data in underwear_data["variants"]:
                    ProductVariant.objects.create(
                        product=product,
                        size=variant_data["size"],
                        color=variant_data["color"],
                        sku=variant_data["sku"],
                        stock_qty=100,
                    )
                self.stdout.write(f"  Created: {underwear_data['name']}")

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully seeded products! Created 2 categories, 6 products, and 15 variants."
            )
        )
