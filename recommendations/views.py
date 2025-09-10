from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Recommendation
from .services import generate_recommendations


@login_required
def my_recommendations(request):
	# Build fresh recommendations each visit for now
	generate_recommendations(request.user)
	recs = Recommendation.objects.filter(user=request.user).order_by("-score")
	return render(request, "recommendations/list.html", {"recs": recs})


