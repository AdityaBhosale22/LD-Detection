from pathlib import Path
from unittest import mock

from botocore.exceptions import ClientError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import UserAccount
from assessments.models import DemographicProfile, MathTestSession

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "ld_model.joblib"
PASSWORD = "S3cure-pass-123"


def setUpModule():
	# The model is a build artifact (gitignored); train it if this checkout lacks it.
	if not MODEL_PATH.exists():
		from ml.build_baseline import main
		main()


class HealthTests(TestCase):
	def test_healthz(self):
		resp = self.client.get("/healthz/")
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.json(), {"status": "ok"})


class AuthTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_register_returns_token_that_works(self):
		resp = self.client.post("/api/auth/register/", {
			"email": "student@example.com", "password": PASSWORD, "first_name": "Asha", "role": "student",
		}, format="json")
		self.assertEqual(resp.status_code, 201)
		token = resp.json()["token"]

		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
		me = self.client.get("/api/auth/me/")
		self.assertEqual(me.json()["email"], "student@example.com")

	def test_register_rejects_weak_password(self):
		resp = self.client.post("/api/auth/register/", {"email": "a@example.com", "password": "123"}, format="json")
		self.assertEqual(resp.status_code, 400)
		self.assertIn("password", resp.json())

	def test_login_and_logout(self):
		UserAccount.objects.create_user("user@example.com", PASSWORD)
		bad = self.client.post("/api/auth/login/", {"email": "user@example.com", "password": "wrong"}, format="json")
		self.assertEqual(bad.status_code, 400)

		resp = self.client.post("/api/auth/login/", {"email": "user@example.com", "password": PASSWORD}, format="json")
		self.assertEqual(resp.status_code, 200)
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {resp.json()['token']}")
		self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
		self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

	def test_endpoints_require_auth(self):
		for url in ["/api/dashboard/", "/api/intake/", "/api/recommendations/", "/api/report/"]:
			self.assertEqual(self.client.get(url).status_code, 401, url)


class ApiTestCase(TestCase):
	def setUp(self):
		self.user = UserAccount.objects.create_user("user@example.com", PASSWORD)
		self.client = APIClient()
		self.client.force_authenticate(self.user)

	def start(self, kind):
		resp = self.client.post(f"/api/tests/{kind}/start/")
		self.assertEqual(resp.status_code, 201)
		return resp.json()

	def submit(self, kind, session_id, payload):
		return self.client.post(f"/api/tests/{kind}/{session_id}/submit/", payload, format="json")


class PredictionFlowTests(ApiTestCase):
	def test_prediction_needs_intake(self):
		self.assertEqual(self.client.post("/api/predictions/").status_code, 400)

	def test_intake_then_prediction(self):
		resp = self.client.post("/api/intake/", {
			"age": 10, "gender": "male", "reading_difficulties": True, "attention_span": "low",
		}, format="json")
		self.assertEqual(resp.status_code, 201)

		resp = self.client.post("/api/predictions/")
		self.assertEqual(resp.status_code, 201)
		self.assertGreaterEqual(resp.json()["probability"], 0.0)
		self.assertLessEqual(resp.json()["probability"], 1.0)
		self.assertEqual(self.client.get("/api/predictions/").json()["id"], resp.json()["id"])

	def test_intake_validates_age(self):
		resp = self.client.post("/api/intake/", {"age": 99, "gender": "male"}, format="json")
		self.assertEqual(resp.status_code, 400)
		self.assertIn("age", resp.json())


class AssessmentTests(ApiTestCase):
	def test_math_scores_answers_and_hides_them_before_submit(self):
		data = self.start("math")
		self.assertNotIn("answer", data["questions"][0])
		answers = [q["a"] + q["b"] if q["op"] == "+" else q["a"] - q["b"] for q in data["questions"]]
		answers[0] = 999  # one wrong
		result = self.submit("math", data["id"], {"answers": answers}).json()
		self.assertEqual(result["num_correct"], 9)
		self.assertEqual(result["num_total"], 10)

	def test_cannot_submit_twice(self):
		data = self.start("grammar")
		self.assertNotIn("answer", data["questions"][0])
		self.assertEqual(self.submit("grammar", data["id"], {"answers": []}).status_code, 200)
		self.assertEqual(self.submit("grammar", data["id"], {"answers": []}).status_code, 400)

	def test_reading_memory_and_scenario(self):
		reading = self.start("reading")
		result = self.submit("reading", reading["id"], {"transcript": reading["passage"], "reading_seconds": 6}).json()
		self.assertEqual(result["accuracy"], 1.0)
		self.assertGreater(result["wpm"], 0)

		memory = self.start("memory")
		result = self.submit("memory", memory["id"], {"response": memory["sequence"]}).json()
		self.assertEqual(result["num_correct"], 6)

		scenario = self.start("scenario")
		self.assertNotIn("a", scenario["questions"][0])
		result = self.submit("scenario", scenario["id"], {"answers": []}).json()
		self.assertEqual(result["num_correct"], 0)

	def test_cannot_access_another_users_test(self):
		other = UserAccount.objects.create_user("other@example.com", PASSWORD)
		session = MathTestSession.objects.create(user=other, num_total=0, details=[])
		self.assertEqual(self.client.get(f"/api/tests/math/{session.id}/").status_code, 404)

	def test_unknown_test_kind(self):
		self.assertEqual(self.client.post("/api/tests/chess/start/").status_code, 404)

	def test_unfinished_tests_do_not_count(self):
		self.start("math")  # started, never submitted
		dashboard = self.client.get("/api/dashboard/").json()
		self.assertIsNone(dashboard["tests"]["math"])
		self.assertEqual(dashboard["areas"], [])


class ReportTests(ApiTestCase):
	def setUp(self):
		super().setUp()
		DemographicProfile.objects.create(user=self.user, age=10, gender="female")
		data = self.start("math")
		self.submit("math", data["id"], {"answers": [0] * 10})
		memory = self.start("memory")
		self.submit("memory", memory["id"], {"response": memory["sequence"]})

	def test_dashboard_and_recommendations(self):
		dashboard = self.client.get("/api/dashboard/").json()
		self.assertEqual(dashboard["tests"]["math"]["num_total"], 10)
		self.assertIsNone(dashboard["tests"]["reading"])
		self.assertEqual({a["area"] for a in dashboard["areas"]}, {"math", "memory"})

		recs = self.client.get("/api/recommendations/").json()
		self.assertTrue(any(r["area"] == "math" for r in recs))

	@override_settings(AWS_S3_REPORTS_BUCKET="")
	@mock.patch("reports.storage.boto3.client")
	def test_report_is_a_pdf_and_skips_s3_without_bucket(self, client):
		resp = self.client.get("/api/report/")
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp["Content-Type"], "application/pdf")
		self.assertTrue(resp.content.startswith(b"%PDF"))
		client.assert_not_called()

	@override_settings(AWS_S3_REPORTS_BUCKET="ld-reports-test")
	@mock.patch("reports.storage.boto3.client")
	def test_report_uploaded_to_s3(self, client):
		resp = self.client.get("/api/report/")
		put = client.return_value.put_object
		put.assert_called_once()
		kwargs = put.call_args.kwargs
		self.assertEqual(kwargs["Bucket"], "ld-reports-test")
		self.assertTrue(kwargs["Key"].startswith(f"reports/user-{self.user.pk}/"))
		self.assertEqual(kwargs["Body"], resp.content)

	@override_settings(AWS_S3_REPORTS_BUCKET="ld-reports-test")
	@mock.patch("reports.storage.boto3.client")
	def test_s3_failure_does_not_break_download(self, client):
		client.return_value.put_object.side_effect = ClientError(
			{"Error": {"Code": "AccessDenied", "Message": "denied"}}, "PutObject"
		)
		with self.assertLogs("reports.storage", level="ERROR"):
			resp = self.client.get("/api/report/")
		self.assertEqual(resp.status_code, 200)


class CorsTests(TestCase):
	@override_settings(CORS_ALLOWED_ORIGINS=["https://ld-detect.vercel.app"])
	def test_frontend_origin_allowed(self):
		resp = self.client.options(
			"/api/auth/login/",
			HTTP_ORIGIN="https://ld-detect.vercel.app",
			HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
		)
		self.assertEqual(resp["Access-Control-Allow-Origin"], "https://ld-detect.vercel.app")
