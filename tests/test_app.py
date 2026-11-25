from pathlib import Path
from unittest import mock

from botocore.exceptions import ClientError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import UserAccount
from assessments.models import DemographicProfile, MathTestSession
from predictions.models import PredictionResult

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "ld_model.joblib"


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
	def test_register_logs_user_in(self):
		resp = self.client.post(reverse("register"), {
			"email": "student@example.com",
			"first_name": "Test",
			"last_name": "Student",
			"role": "student",
			"password1": "S3cure-pass-123",
			"password2": "S3cure-pass-123",
		})
		self.assertRedirects(resp, reverse("home"))
		self.assertTrue(UserAccount.objects.filter(email="student@example.com").exists())

	def test_pages_require_login(self):
		for url in ["/assessments/intake/", "/reports/download/", "/recommendations/"]:
			resp = self.client.get(url)
			self.assertEqual(resp.status_code, 302, url)
			self.assertIn("/accounts/login/", resp["Location"])


class LoggedInTestCase(TestCase):
	def setUp(self):
		self.user = UserAccount.objects.create_user("user@example.com", "S3cure-pass-123")
		self.client.force_login(self.user)


class PredictionFlowTests(LoggedInTestCase):
	def test_intake_then_prediction(self):
		resp = self.client.post(reverse("demographic_intake"), {
			"age": 10,
			"gender": "male",
			"reading_difficulties": "on",
			"attention_span": "low",
		})
		self.assertRedirects(resp, reverse("intake_success"))
		profile = DemographicProfile.objects.get(user=self.user)

		resp = self.client.get(reverse("predict_from_intake", args=[profile.id]))
		prediction = PredictionResult.objects.get(user=self.user)
		self.assertRedirects(resp, reverse("prediction_detail", args=[prediction.id]))
		self.assertGreaterEqual(prediction.probability, 0.0)
		self.assertLessEqual(prediction.probability, 1.0)

	def test_cannot_predict_on_another_users_intake(self):
		other = UserAccount.objects.create_user("other@example.com", "S3cure-pass-123")
		profile = DemographicProfile.objects.create(user=other, age=9, gender="female")
		resp = self.client.get(reverse("predict_from_intake", args=[profile.id]))
		self.assertEqual(resp.status_code, 404)


class MathTestTests(LoggedInTestCase):
	def test_submit_scores_answers(self):
		self.client.get(reverse("math_test_start"))
		questions = self.client.session["math_questions"]
		answers = {
			f"q_{i}": (q["a"] + q["b"] if q["op"] == "+" else q["a"] - q["b"])
			for i, q in enumerate(questions)
		}
		self.client.post(reverse("math_test_submit"), answers)
		session = MathTestSession.objects.get(user=self.user)
		self.assertEqual(session.num_correct, len(questions))


class ReportTests(LoggedInTestCase):
	def test_report_is_a_pdf(self):
		resp = self.client.get(reverse("download_report"))
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp["Content-Type"], "application/pdf")
		self.assertTrue(resp.content.startswith(b"%PDF"))

	def test_dashboard_and_recommendations_render(self):
		self.assertEqual(self.client.get(reverse("analytics_dashboard")).status_code, 200)
		self.assertEqual(self.client.get("/recommendations/").status_code, 200)

	@override_settings(AWS_S3_REPORTS_BUCKET="")
	@mock.patch("reports.storage.boto3.client")
	def test_no_s3_upload_when_bucket_not_set(self, client):
		self.client.get(reverse("download_report"))
		client.assert_not_called()

	@override_settings(AWS_S3_REPORTS_BUCKET="ld-reports-test")
	@mock.patch("reports.storage.boto3.client")
	def test_report_uploaded_to_s3(self, client):
		resp = self.client.get(reverse("download_report"))
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
			resp = self.client.get(reverse("download_report"))
		self.assertEqual(resp.status_code, 200)
