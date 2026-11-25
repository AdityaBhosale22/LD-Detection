from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path, include
from django.shortcuts import render


def home(request):
	return render(request, "home.html")


def healthz(_request):
	"""Liveness check used by Docker HEALTHCHECK, CI smoke test and deploy script."""
	with connection.cursor() as cursor:
		cursor.execute("SELECT 1")
	return JsonResponse({"status": "ok"})


urlpatterns = [
	path("", home, name="home"),
	path("healthz/", healthz, name="healthz"),
	path("admin/", admin.site.urls),
	path("accounts/", include("accounts.urls")),
	path("assessments/", include("assessments.urls")),
	path("predictions/", include("predictions.urls")),
	path("recommendations/", include("recommendations.urls")),
	path("reports/", include("reports.urls")),
]


