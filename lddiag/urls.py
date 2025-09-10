from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def home(_request):
	return HttpResponse("LD Detection Home")


urlpatterns = [
	path("", home, name="home"),
	path("admin/", admin.site.urls),
	path("accounts/", include("accounts.urls")),
]


