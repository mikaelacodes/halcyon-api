from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from apps.core.permissions import IsAdminOrCreateOnly, IsAdminOrReadOnly

from .models import Product, ProductSupplier, StockMovement, Supplier, Warehouse
from .serializers import (
    ProductSerializer,
    ProductSupplierSerializer,
    StockMovementSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ["name", "contact_email"]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ["code", "name"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related("productsupplier_set__supplier")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ["sku", "name"]


class ProductSupplierViewSet(viewsets.ModelViewSet):
    queryset = ProductSupplier.objects.select_related("product", "supplier")
    serializer_class = ProductSupplierSerializer
    permission_classes = [IsAdminOrReadOnly]


class StockMovementViewSet(viewsets.ModelViewSet):
    """Standard users can log movements (create); only admins edit/delete history."""

    queryset = StockMovement.objects.select_related("product", "warehouse", "recorded_by")
    serializer_class = StockMovementSerializer
    permission_classes = [IsAdminOrCreateOnly]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        warehouse = self.request.query_params.get("warehouse")
        product = self.request.query_params.get("product")
        movement_type = self.request.query_params.get("movement_type")
        if warehouse:
            qs = qs.filter(warehouse_id=warehouse)
        if product:
            qs = qs.filter(product_id=product)
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        return qs
