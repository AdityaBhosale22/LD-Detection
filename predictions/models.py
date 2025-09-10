from django.db import models
from django.conf import settings


class PredictionResult(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predictions")
	# Link to intake profile to know what data was used
	intake = models.ForeignKey("assessments.DemographicProfile", on_delete=models.CASCADE, related_name="prediction_results")
	label = models.CharField(max_length=32)  # e.g., "LD Detected" or "No LD Detected"
	probability = models.FloatField()  # probability of LD class
	model_name = models.CharField(max_length=128, default="sklearn_model")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Prediction({self.user_id}, {self.label}, p={self.probability:.2f})"


