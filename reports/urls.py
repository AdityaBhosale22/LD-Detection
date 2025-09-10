from django.urls import path
from .views import download_report, analytics_dashboard


urlpatterns = [
	path("download/", download_report, name="download_report"),
	path("dashboard/", analytics_dashboard, name="analytics_dashboard"),
]


