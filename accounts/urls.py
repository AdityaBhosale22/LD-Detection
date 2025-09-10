from django.urls import path
from .views import register, EmailLoginView, logout_view

urlpatterns = [
	path("register/", register, name="register"),
	path("login/", EmailLoginView.as_view(), name="login"),
	path("logout/", logout_view, name="logout"),
]
