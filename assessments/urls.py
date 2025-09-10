from django.urls import path
from .views import demographic_intake, intake_success


urlpatterns = [
	path("intake/", demographic_intake, name="demographic_intake"),
	path("intake/success/", intake_success, name="intake_success"),
]


