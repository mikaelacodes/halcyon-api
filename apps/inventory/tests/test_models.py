import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.inventory.models import Product, ProductSupplier, Supplier, Warehouse


@pytest.mark.django_db
class TestValidation:
    def test_product_sku_rejects_lowercase(self):
        p = Product(sku="bad-sku", name="X", unit_price="1.00")
        with pytest.raises(ValidationError):
            p.full_clean()

    def test_product_sku_accepts_valid_format(self):
        p = Product(sku="WIDGET-001", name="Widget", unit_price="1.00")
        p.full_clean()  # should not raise

    def test_product_rejects_negative_price(self):
        p = Product(sku="WIDGET-001", name="Widget", unit_price="-1.00")
        with pytest.raises(ValidationError):
            p.full_clean()

    def test_warehouse_code_rejects_lowercase(self):
        w = Warehouse(code="sea1", name="Seattle DC")
        with pytest.raises(ValidationError):
            w.full_clean()

    def test_stock_movement_quantity_must_be_positive(self, product, warehouse):
        from apps.inventory.models import StockMovement

        movement = StockMovement(
            product=product, warehouse=warehouse, movement_type="RECEIPT", quantity=0
        )
        with pytest.raises(ValidationError):
            movement.full_clean()


@pytest.mark.django_db
class TestRelationships:
    def test_product_supplier_m2m_through(self, product, supplier):
        ProductSupplier.objects.create(product=product, supplier=supplier, lead_time_days=3)
        assert supplier in product.suppliers.all()

    def test_product_supplier_pair_must_be_unique(self, product, supplier):
        ProductSupplier.objects.create(product=product, supplier=supplier)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductSupplier.objects.create(product=product, supplier=supplier)

    def test_supplier_name_must_be_unique(self):
        Supplier.objects.create(name="Acme Co", contact_email="a@acme.test")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Supplier.objects.create(name="Acme Co", contact_email="b@acme.test")
