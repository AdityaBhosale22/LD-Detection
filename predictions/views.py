from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from assessments.models import DemographicProfile
from .models import PredictionResult
from .services import LDClassifier, default_model_spec


def serialize_prediction(prediction):
	if prediction is None:
		return None
	return {
		"id": prediction.id,
		"label": prediction.label,
		"probability": round(prediction.probability, 4),
		"intake_id": prediction.intake_id,
		"created_at": prediction.created_at,
	}


@api_view(["GET", "POST"])
def predictions(request):
	"""GET the latest prediction, or POST to run the model on the latest intake."""
	if request.method == "GET":
		return Response(serialize_prediction(PredictionResult.objects.filter(user=request.user).first()))

	profile = DemographicProfile.objects.filter(user=request.user).first()
	if profile is None:
		return Response({"detail": "Complete the intake form first."}, status=status.HTTP_400_BAD_REQUEST)

	result = LDClassifier(default_model_spec()).predict(profile)
	prediction = PredictionResult.objects.create(
		user=request.user,
		intake=profile,
		label=result["label"],
		probability=result["probability"],
		model_name="logistic_regression_baseline",
	)
	return Response(serialize_prediction(prediction), status=status.HTTP_201_CREATED)
