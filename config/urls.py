from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.inventory.urls")),
]

handler404 = "apps.core.views.not_found_view"
handler500 = "apps.core.views.server_error_view"
