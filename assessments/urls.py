from django.urls import path
from .views import (
	demographic_intake,
	intake_success,
	math_test_start,
	math_test_submit,
	math_test_result,
	grammar_test_start,
	grammar_test_submit,
	grammar_test_result,
	reading_test_start,
	reading_test_submit,
	reading_test_result,
)


urlpatterns = [
	path("intake/", demographic_intake, name="demographic_intake"),
	path("intake/success/", intake_success, name="intake_success"),
	path("math/start/", math_test_start, name="math_test_start"),
	path("math/submit/", math_test_submit, name="math_test_submit"),
	path("math/result/<int:session_id>/", math_test_result, name="math_test_result"),
	path("grammar/start/", grammar_test_start, name="grammar_test_start"),
	path("grammar/submit/", grammar_test_submit, name="grammar_test_submit"),
	path("grammar/result/<int:session_id>/", grammar_test_result, name="grammar_test_result"),
	path("reading/start/", reading_test_start, name="reading_test_start"),
	path("reading/submit/", reading_test_submit, name="reading_test_submit"),
	path("reading/result/<int:session_id>/", reading_test_result, name="reading_test_result"),
]


