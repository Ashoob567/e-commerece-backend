from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Category, Product, ProductTag


@receiver(pre_save, sender=Category)
def auto_generate_category_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


@receiver(pre_save, sender=Product)
def auto_generate_product_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)


@receiver(pre_save, sender=ProductTag)
def auto_generate_product_tag_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.name)
