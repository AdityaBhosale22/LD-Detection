from django.conf import settings
from django.db import models


class DemographicProfile(models.Model):
	GENDER_CHOICES = [
		("male", "Male"),
		("female", "Female"),
		("other", "Other"),
	]
	ATTENTION_CHOICES = [
		("low", "Low"),
		("medium", "Medium"),
		("high", "High"),
	]

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demographics")
	age = models.PositiveIntegerField()
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
	academic_history = models.TextField(blank=True)
	reading_difficulties = models.BooleanField(default=False)
	attention_span = models.CharField(max_length=10, choices=ATTENTION_CHOICES, default="medium")
	learning_issues_notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Demographics({self.user.email}, age={self.age})"


