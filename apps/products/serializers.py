from rest_framework import serializers

from .models import Category, Product, ProductImage, ProductTag, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="parent", required=False, allow_null=True
    )

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "image", "parent_id", "children"]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "url", "alt_text", "is_primary", "order"]

    def get_url(self, obj):
        """Return the Supabase public URL."""
        if obj.image_url:
            return obj.image_url
        if obj.image:
            try:
                return obj.image.url
            except Exception:
                return None
        return None


class ProductVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "size", "color", "sku", "stock_qty", "final_price", "is_in_stock"]


class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    is_on_sale = serializers.BooleanField(read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    average_rating = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "base_price",
            "sale_price",
            "discount_percentage",
            "is_on_sale",
            "is_featured",
            "primary_image",
            "category",
            "average_rating",
            "is_in_stock",
        ]

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        return None

    def get_average_rating(self, obj):
        return getattr(obj, "average_rating", None)

    def get_is_in_stock(self, obj):
        return obj.variants.filter(stock_qty__gt=0).exists()


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    tags = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=ProductTag.objects.all()
    )
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "base_price",
            "sale_price",
            "is_featured",
            "is_active",
            "tags",
            "created_at",
            "updated_at",
            "images",
            "variants",
            "average_rating",
            "review_count",
        ]

    def get_average_rating(self, obj):
        return getattr(obj, "average_rating", None)

    def get_review_count(self, obj):
        return getattr(obj, "review_count", 0)
