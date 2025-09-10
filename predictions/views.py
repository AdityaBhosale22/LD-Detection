from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from assessments.models import DemographicProfile
from .models import PredictionResult
from .services import LDClassifier, default_model_spec


@login_required
def predict_from_intake(request, intake_id: int):
	profile = get_object_or_404(DemographicProfile, pk=intake_id, user=request.user)
	classifier = LDClassifier(default_model_spec())
	result = classifier.predict(profile)
	prediction = PredictionResult.objects.create(
		user=request.user,
		intake=profile,
		label=result["label"],
		probability=result["probability"],
		model_name="sklearn",
	)
	return redirect(reverse("prediction_detail", args=[prediction.id]))


@login_required
def prediction_detail(request, prediction_id: int):
	prediction = get_object_or_404(PredictionResult, pk=prediction_id, user=request.user)
	return render(request, "predictions/detail.html", {"prediction": prediction})


