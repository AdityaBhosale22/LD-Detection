from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def index(_request):
	return JsonResponse({"name": "LD Detection API", "health": "/healthz/", "api": "/api/"})


# /healthz/ is answered by lddiag.middleware.HealthCheckMiddleware.
urlpatterns = [
	path("", index),
	path("admin/", admin.site.urls),
	path("api/auth/", include("accounts.urls")),
	path("api/", include("assessments.urls")),
	path("api/predictions/", include("predictions.urls")),
	path("api/recommendations/", include("recommendations.urls")),
	path("api/", include("reports.urls")),
]
