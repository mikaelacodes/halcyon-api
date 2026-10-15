from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

SKU_VALIDATOR = RegexValidator(
    r"^[A-Z0-9-]{3,32}$", "SKU must be 3-32 uppercase letters, digits or hyphens."
)
WAREHOUSE_CODE_VALIDATOR = RegexValidator(
    r"^[A-Z0-9]{2,10}$", "Warehouse code must be 2-10 uppercase letters/digits."
)


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    code = models.CharField(max_length=10, unique=True, validators=[WAREHOUSE_CODE_VALIDATOR])
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Product(models.Model):
    sku = models.CharField(max_length=32, unique=True, validators=[SKU_VALIDATOR])
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    reorder_threshold = models.PositiveIntegerField(default=0)
    suppliers = models.ManyToManyField(
        Supplier, through="ProductSupplier", related_name="products"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sku"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.sku} — {self.name}"


class ProductSupplier(models.Model):
    """Through table: which suppliers can fulfil a product, and on what terms."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    supplier_sku = models.CharField(max_length=64, blank=True)
    lead_time_days = models.PositiveSmallIntegerField(default=1)
    is_preferred = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "supplier"], name="unique_product_supplier"
            )
        ]

    def __str__(self):
        return f"{self.product.sku} <- {self.supplier.name}"


class StockMovement(models.Model):
    """An inbound/outbound/adjustment transaction against a product's stock at a warehouse."""

    class MovementType(models.TextChoices):
        RECEIPT = "RECEIPT", "Receipt"
        SHIPMENT = "SHIPMENT", "Shipment"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_movements",
    )
    reference_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "warehouse"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} x {self.product.sku} @ {self.warehouse.code}"
