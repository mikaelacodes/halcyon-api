from django.contrib import admin

from .models import Product, ProductSupplier, StockMovement, Supplier, Warehouse


class ProductSupplierInline(admin.TabularInline):
    model = ProductSupplier
    extra = 1


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "is_active")
    search_fields = ("name", "contact_email")
    list_filter = ("is_active",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "location")
    search_fields = ("code", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "unit_price", "reorder_threshold", "is_active")
    search_fields = ("sku", "name")
    list_filter = ("is_active",)
    inlines = [ProductSupplierInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "movement_type",
        "product",
        "warehouse",
        "quantity",
        "recorded_by",
    )
    list_filter = ("movement_type", "warehouse")
    search_fields = ("product__sku", "reference_note")
    date_hierarchy = "created_at"
