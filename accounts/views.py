from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import RegistrationForm, EmailAuthenticationForm


def register(request):
	if request.method == "POST":
		form = RegistrationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful.")
			return redirect("home")
	else:
		form = RegistrationForm()
	return render(request, "accounts/register.html", {"form": form})


class EmailLoginView(LoginView):
	template_name = "accounts/login.html"
	form_class = EmailAuthenticationForm
	redirect_authenticated_user = True
	success_url = reverse_lazy("home")


def logout_view(request):
	logout(request)
	messages.info(request, "Logged out.")
	return redirect("login")
