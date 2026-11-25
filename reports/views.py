from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from accounts.serializers import UserSerializer
from assessments.engine import TESTS
from assessments.models import DemographicProfile
from assessments.serializers import DemographicProfileSerializer
from predictions.models import PredictionResult
from predictions.views import serialize_prediction
from recommendations.services import compute_user_area_scores, generate_recommendations
from .pdf import build_report_pdf
from .storage import upload_report


@api_view(["GET"])
def dashboard(request):
	"""Everything the dashboard page needs in one request."""
	user = request.user
	profile = DemographicProfile.objects.filter(user=user).first()

	tests = {}
	for kind, test in TESTS.items():
		latest = test.model.objects.filter(user=user, ended_at__isnull=False).order_by("-started_at").first()
		if latest is None:
			tests[kind] = None
			continue
		summary = test.result(latest)
		summary.pop("details", None)
		summary["completed_at"] = latest.ended_at
		tests[kind] = summary

	return Response({
		"user": UserSerializer(user).data,
		"intake": DemographicProfileSerializer(profile).data if profile else None,
		"prediction": serialize_prediction(PredictionResult.objects.filter(user=user).first()),
		"tests": tests,
		"areas": [{"area": a.area, "score": round(a.score, 2)} for a in compute_user_area_scores(user)],
	})


@api_view(["GET"])
def download_report(request):
	"""Generate the PDF report, archive it to S3 (if configured) and return it."""
	generate_recommendations(request.user)
	pdf = build_report_pdf(request.user)
	upload_report(pdf, request.user.pk)
	response = HttpResponse(pdf, content_type="application/pdf")
	response["Content-Disposition"] = 'attachment; filename="ld_report.pdf"'
	return response
