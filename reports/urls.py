from django.urls import path

from . import views

urlpatterns = [
	path("dashboard/", views.dashboard, name="dashboard"),
	path("report/", views.download_report, name="download_report"),
]
