from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import generate_recommendations


@api_view(["GET"])
def recommendations(request):
	"""Rebuild recommendations from completed tests and return them, weakest area first."""
	recs = sorted(generate_recommendations(request.user), key=lambda r: r.score, reverse=True)
	return Response([
		{
			"area": r.area,
			"area_label": r.get_area_display(),
			"title": r.title,
			"description": r.description,
			"url": r.url,
			"score": round(r.score, 2),
		}
		for r in recs
	])
