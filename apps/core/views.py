from django.db import Error as DjangoDBError
from django.db import connections
from django.http import JsonResponse
from django.utils import timezone
from django.views import defaults
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

# Set once per process at import time, so uptime reflects this worker's age
# (the conventional meaning for a health endpoint under gunicorn's
# multi-process model) rather than resetting on every request.
PROCESS_STARTED_AT = timezone.now()


class HealthCheckSerializer(serializers.Serializer):
    """Documents the /health/ response shape for the OpenAPI schema; not used for input."""

    status = serializers.ChoiceField(choices=["ok", "unhealthy"])
    uptime_seconds = serializers.FloatField()
    database = serializers.DictField()


class HealthCheckView(APIView):
    """Liveness/readiness probe for load balancers and docker-compose healthchecks."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(responses=HealthCheckSerializer, tags=["health"])
    def get(self, request):
        db_connected, db_engine = self._check_database()
        uptime_seconds = (timezone.now() - PROCESS_STARTED_AT).total_seconds()

        body = {
            "status": "ok" if db_connected else "unhealthy",
            "uptime_seconds": round(uptime_seconds, 2),
            "database": {"connected": db_connected, "engine": db_engine},
        }
        http_status = status.HTTP_200_OK if db_connected else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(body, status=http_status)

    @staticmethod
    def _check_database():
        conn = connections["default"]
        try:
            conn.cursor().execute("SELECT 1")
        except DjangoDBError:
            return False, None
        return True, conn.settings_dict.get("ENGINE", "").rsplit(".", 1)[-1]


def not_found_view(request, exception=None):
    if not request.path.startswith("/api/"):
        return defaults.page_not_found(request, exception)
    return JsonResponse(
        {
            "error": {
                "code": "not_found",
                "message": "The requested resource was not found.",
            }
        },
        status=404,
    )


def server_error_view(request):
    if not request.path.startswith("/api/"):
        return defaults.server_error(request)
    return JsonResponse(
        {"error": {"code": "server_error", "message": "An unexpected error occurred."}},
        status=500,
    )
