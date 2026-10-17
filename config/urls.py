from django.contrib import admin
from django.urls import include, path

from apps.core.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.inventory.urls")),
]

handler404 = "apps.core.views.not_found_view"
handler500 = "apps.core.views.server_error_view"
