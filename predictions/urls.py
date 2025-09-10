from django.urls import path
from .views import predict_from_intake, prediction_detail


urlpatterns = [
	path("from-intake/<int:intake_id>/", predict_from_intake, name="predict_from_intake"),
	path("detail/<int:prediction_id>/", prediction_detail, name="prediction_detail"),
]


