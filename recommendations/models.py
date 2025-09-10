from django.conf import settings
from django.db import models


class Recommendation(models.Model):
	AREA_CHOICES = [
		("math", "Math"),
		("grammar", "Grammar"),
		("reading", "Reading"),
		("memory", "Memory"),
		("scenario", "Comprehension"),
	]

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations")
	area = models.CharField(max_length=20, choices=AREA_CHOICES)
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	url = models.URLField(blank=True)
	score = models.FloatField(default=0.0)  # normalized weakness severity 0..1
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Rec({self.user_id}, {self.area}, {self.title})"


