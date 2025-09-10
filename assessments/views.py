from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import DemographicProfileForm
from .models import DemographicProfile


@login_required
def demographic_intake(request):
	if request.method == "POST":
		form = DemographicProfileForm(request.POST)
		if form.is_valid():
			profile: DemographicProfile = form.save(commit=False)
			profile.user = request.user
			profile.save()
			return redirect(reverse("intake_success"))
	else:
		form = DemographicProfileForm()
	return render(request, "assessments/demographic_intake.html", {"form": form})


@login_required
def intake_success(_request):
	return render(_request, "assessments/intake_success.html")


