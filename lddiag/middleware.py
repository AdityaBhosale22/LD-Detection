from django.db import connection
from django.http import JsonResponse


class HealthCheckMiddleware:
	"""Answer /healthz/ before any other middleware runs.

	Load balancers and platform health checkers (Render, AWS ALB, Docker) often call the app
	by IP or an internal hostname that is not in ALLOWED_HOSTS. Handling the check here,
	ahead of Django's host validation, keeps it working everywhere. It still checks the database.
	"""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if request.path == "/healthz/":
			with connection.cursor() as cursor:
				cursor.execute("SELECT 1")
			return JsonResponse({"status": "ok"})
		return self.get_response(request)
