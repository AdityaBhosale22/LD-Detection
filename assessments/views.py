from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .engine import TESTS, SubmissionError
from .models import DemographicProfile
from .serializers import DemographicProfileSerializer


@api_view(["GET", "POST"])
def intake(request):
	"""GET the latest intake profile, or POST a new one."""
	if request.method == "POST":
		serializer = DemographicProfileSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save(user=request.user)
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	profile = DemographicProfile.objects.filter(user=request.user).first()
	return Response(DemographicProfileSerializer(profile).data if profile else None)


def _get_test(kind):
	if kind not in TESTS:
		raise Http404("Unknown test")
	return TESTS[kind]


@api_view(["POST"])
def start_test(request, kind):
	test = _get_test(kind)
	session = test.start(request.user)
	return Response({"id": session.id, "kind": kind, **test.public(session)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def submit_test(request, kind, session_id):
	test = _get_test(kind)
	session = get_object_or_404(test.model, pk=session_id, user=request.user)
	try:
		test.submit(session, request.data)
	except SubmissionError as exc:
		return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
	return Response(test.result(session))


@api_view(["GET"])
def test_result(request, kind, session_id):
	test = _get_test(kind)
	session = get_object_or_404(test.model, pk=session_id, user=request.user)
	return Response(test.result(session))
