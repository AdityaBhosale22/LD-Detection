from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path


def index(_request):
	return JsonResponse({"name": "LD Detection API", "health": "/healthz/", "api": "/api/"})


def healthz(_request):
	"""Liveness check used by Docker HEALTHCHECK, CI, Render and the deploy script."""
	with connection.cursor() as cursor:
		cursor.execute("SELECT 1")
	return JsonResponse({"status": "ok"})


urlpatterns = [
	path("", index),
	path("healthz/", healthz, name="healthz"),
	path("admin/", admin.site.urls),
	path("api/auth/", include("accounts.urls")),
	path("api/", include("assessments.urls")),
	path("api/predictions/", include("predictions.urls")),
	path("api/recommendations/", include("recommendations.urls")),
	path("api/", include("reports.urls")),
]
