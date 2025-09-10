from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def home(_request):
	return HttpResponse('<a href="/accounts/login/">Login</a> | <a href="/accounts/register/">Register</a> | <a href="/assessments/intake/">LD Intake</a> | <a href="/assessments/math/start/">Math</a> | <a href="/assessments/grammar/start/">Grammar</a> | <a href="/assessments/reading/start/">Reading</a> | <a href="/assessments/memory/start/">Memory</a> | <a href="/assessments/scenario/start/">Scenario</a> | <a href="/recommendations/">Recommendations</a> | <a href="/reports/dashboard/">Analytics</a> | <a href="/reports/download/">Download Report</a>')


urlpatterns = [
	path("", home, name="home"),
	path("admin/", admin.site.urls),
	path("accounts/", include("accounts.urls")),
	path("assessments/", include("assessments.urls")),
	path("predictions/", include("predictions.urls")),
	path("recommendations/", include("recommendations.urls")),
	path("reports/", include("reports.urls")),
]


