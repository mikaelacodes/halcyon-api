import pytest

from apps.inventory.models import ProductSupplier, StockMovement, Warehouse


@pytest.mark.django_db
class TestSupplierPermissions:
    def test_list_requires_authentication(self, api_client):
        assert api_client.get("/api/suppliers/").status_code == 401

    def test_standard_user_can_list(self, standard_client, supplier):
        resp = standard_client.get("/api/suppliers/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    def test_standard_user_cannot_create(self, standard_client):
        resp = standard_client.post(
            "/api/suppliers/", {"name": "New Co", "contact_email": "n@co.test"}
        )
        assert resp.status_code == 403

    def test_admin_can_create(self, admin_client):
        resp = admin_client.post(
            "/api/suppliers/", {"name": "New Co", "contact_email": "n@co.test"}
        )
        assert resp.status_code == 201

    def test_admin_can_update_and_delete(self, admin_client, supplier):
        resp = admin_client.patch(f"/api/suppliers/{supplier.id}/", {"phone": "555-0100"})
        assert resp.status_code == 200
        resp = admin_client.delete(f"/api/suppliers/{supplier.id}/")
        assert resp.status_code == 204


@pytest.mark.django_db
class TestWarehousePermissions:
    def test_standard_user_cannot_create(self, standard_client):
        resp = standard_client.post("/api/warehouses/", {"code": "SEA1", "name": "Seattle DC"})
        assert resp.status_code == 403

    def test_admin_can_create(self, admin_client):
        resp = admin_client.post("/api/warehouses/", {"code": "SEA1", "name": "Seattle DC"})
        assert resp.status_code == 201

    def test_rejects_invalid_code_format(self, admin_client):
        resp = admin_client.post("/api/warehouses/", {"code": "sea1", "name": "Seattle DC"})
        assert resp.status_code == 400


@pytest.mark.django_db
class TestProductPermissions:
    def test_standard_user_can_read_but_not_write(self, standard_client, product):
        assert standard_client.get(f"/api/products/{product.id}/").status_code == 200
        resp = standard_client.patch(f"/api/products/{product.id}/", {"name": "Renamed"})
        assert resp.status_code == 403

    def test_admin_can_create_product(self, admin_client):
        resp = admin_client.post(
            "/api/products/", {"sku": "GADGET-002", "name": "Gadget", "unit_price": "19.99"}
        )
        assert resp.status_code == 201

    def test_product_detail_shows_linked_suppliers(self, admin_client, product, supplier):
        ProductSupplier.objects.create(product=product, supplier=supplier, lead_time_days=3)
        resp = admin_client.get(f"/api/products/{product.id}/")
        assert resp.status_code == 200
        suppliers = resp.json()["suppliers"]
        assert len(suppliers) == 1
        assert suppliers[0]["supplier_name"] == supplier.name


@pytest.mark.django_db
class TestProductSupplierLink:
    def test_admin_can_link_supplier_to_product(self, admin_client, product, supplier):
        resp = admin_client.post(
            "/api/product-suppliers/",
            {"product": product.id, "supplier": supplier.id, "lead_time_days": 5},
        )
        assert resp.status_code == 201

    def test_duplicate_link_is_rejected(self, admin_client, product, supplier):
        ProductSupplier.objects.create(product=product, supplier=supplier)
        resp = admin_client.post(
            "/api/product-suppliers/", {"product": product.id, "supplier": supplier.id}
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestStockMovements:
    def test_standard_user_can_record_a_movement(self, standard_client, product, warehouse):
        resp = standard_client.post(
            "/api/stock-movements/",
            {
                "product": product.id,
                "warehouse": warehouse.id,
                "movement_type": "RECEIPT",
                "quantity": 50,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["recorded_by"] == "standard"

    def test_recorded_by_cannot_be_spoofed(self, standard_client, admin_user, product, warehouse):
        resp = standard_client.post(
            "/api/stock-movements/",
            {
                "product": product.id,
                "warehouse": warehouse.id,
                "movement_type": "RECEIPT",
                "quantity": 50,
                "recorded_by": admin_user.id,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["recorded_by"] == "standard"

    def test_standard_user_cannot_delete_a_movement(self, standard_client, product, warehouse):
        movement = StockMovement.objects.create(
            product=product, warehouse=warehouse, movement_type="RECEIPT", quantity=10
        )
        resp = standard_client.delete(f"/api/stock-movements/{movement.id}/")
        assert resp.status_code == 403

    def test_admin_can_delete_a_movement(self, admin_client, product, warehouse):
        movement = StockMovement.objects.create(
            product=product, warehouse=warehouse, movement_type="RECEIPT", quantity=10
        )
        resp = admin_client.delete(f"/api/stock-movements/{movement.id}/")
        assert resp.status_code == 204

    def test_filter_by_warehouse(self, admin_client, product, warehouse):
        other_warehouse = Warehouse.objects.create(code="LAX1", name="LA DC")
        StockMovement.objects.create(
            product=product, warehouse=warehouse, movement_type="RECEIPT", quantity=10
        )
        StockMovement.objects.create(
            product=product, warehouse=other_warehouse, movement_type="RECEIPT", quantity=5
        )
        resp = admin_client.get(f"/api/stock-movements/?warehouse={warehouse.id}")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["warehouse"] == warehouse.id

    def test_filter_by_movement_type(self, admin_client, product, warehouse):
        StockMovement.objects.create(
            product=product, warehouse=warehouse, movement_type="RECEIPT", quantity=10
        )
        StockMovement.objects.create(
            product=product, warehouse=warehouse, movement_type="SHIPMENT", quantity=3
        )
        resp = admin_client.get("/api/stock-movements/?movement_type=SHIPMENT")
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["movement_type"] == "SHIPMENT"

    def test_deleting_product_with_movements_is_conflict_not_500(
        self, admin_client, product, warehouse
    ):
        StockMovement.objects.create(
            product=product, warehouse=warehouse, movement_type="RECEIPT", quantity=10
        )
        resp = admin_client.delete(f"/api/products/{product.id}/")
        assert resp.status_code == 409
