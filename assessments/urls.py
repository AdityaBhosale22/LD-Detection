from django.urls import path

from . import views

urlpatterns = [
	path("intake/", views.intake, name="intake"),
	path("tests/<str:kind>/start/", views.start_test, name="test_start"),
	path("tests/<str:kind>/<int:session_id>/", views.test_result, name="test_result"),
	path("tests/<str:kind>/<int:session_id>/submit/", views.submit_test, name="test_submit"),
]
