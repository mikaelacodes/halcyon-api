from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.inventory.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

handler404 = "apps.core.views.not_found_view"
handler500 = "apps.core.views.server_error_view"
