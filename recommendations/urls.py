from django.urls import path
from .views import my_recommendations


urlpatterns = [
	path("", my_recommendations, name="my_recommendations"),
]


