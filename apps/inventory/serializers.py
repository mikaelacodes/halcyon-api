from rest_framework import serializers

from .models import Product, ProductSupplier, StockMovement, Supplier, Warehouse


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_email", "phone", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name", "location"]
        read_only_fields = ["id"]


class ProductSupplierSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = ProductSupplier
        fields = [
            "id",
            "product",
            "supplier",
            "supplier_name",
            "supplier_sku",
            "lead_time_days",
            "is_preferred",
        ]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):
    suppliers = ProductSupplierSerializer(source="productsupplier_set", many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "unit_price",
            "reorder_threshold",
            "is_active",
            "suppliers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    recorded_by = serializers.ReadOnlyField(source="recorded_by.username")
    product_sku = serializers.ReadOnlyField(source="product.sku")
    warehouse_code = serializers.ReadOnlyField(source="warehouse.code")

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_sku",
            "warehouse",
            "warehouse_code",
            "movement_type",
            "quantity",
            "recorded_by",
            "reference_note",
            "created_at",
        ]
        read_only_fields = ["id", "recorded_by", "created_at"]
