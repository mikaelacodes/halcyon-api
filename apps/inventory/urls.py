from rest_framework.routers import DefaultRouter

from .views import (
    ProductSupplierViewSet,
    ProductViewSet,
    StockMovementViewSet,
    SupplierViewSet,
    WarehouseViewSet,
)

router = DefaultRouter()
router.register("suppliers", SupplierViewSet)
router.register("warehouses", WarehouseViewSet)
router.register("products", ProductViewSet)
router.register("product-suppliers", ProductSupplierViewSet)
router.register("stock-movements", StockMovementViewSet)

urlpatterns = router.urls
