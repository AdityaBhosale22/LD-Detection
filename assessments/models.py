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


class MathTestSession(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="math_tests")
	started_at = models.DateTimeField(auto_now_add=True)
	ended_at = models.DateTimeField(null=True, blank=True)
	num_correct = models.PositiveIntegerField(default=0)
	num_total = models.PositiveIntegerField(default=0)
	duration_seconds = models.PositiveIntegerField(default=0)
	# Store per-question details: [{"a": int, "b": int, "op": "+", "answer": int, "user": int, "correct": bool}]
	details = models.JSONField(default=list, blank=True)

	class Meta:
		ordering = ["-started_at"]

	def __str__(self) -> str:
		return f"MathTest(user={self.user_id}, {self.num_correct}/{self.num_total})"


class GrammarTestSession(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grammar_tests")
	started_at = models.DateTimeField(auto_now_add=True)
	ended_at = models.DateTimeField(null=True, blank=True)
	num_correct = models.PositiveIntegerField(default=0)
	num_total = models.PositiveIntegerField(default=0)
	duration_seconds = models.PositiveIntegerField(default=0)
	# details: [{"prompt": str, "options": [str,...], "answer": str, "user": str, "correct": bool}]
	details = models.JSONField(default=list, blank=True)

	class Meta:
		ordering = ["-started_at"]

	def __str__(self) -> str:
		return f"GrammarTest(user={self.user_id}, {self.num_correct}/{self.num_total})"


class ReadingTestSession(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reading_tests")
	started_at = models.DateTimeField(auto_now_add=True)
	ended_at = models.DateTimeField(null=True, blank=True)
	passage = models.TextField()
	transcript = models.TextField(blank=True)
	duration_seconds = models.PositiveIntegerField(default=0)
	wpm = models.FloatField(default=0.0)
	accuracy = models.FloatField(default=0.0)  # 0..1 token overlap
	details = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ["-started_at"]

	def __str__(self) -> str:
		return f"ReadingTest(user={self.user_id}, wpm={self.wpm:.1f}, acc={self.accuracy:.2f})"


class MemoryTestSession(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memory_tests")
	started_at = models.DateTimeField(auto_now_add=True)
	ended_at = models.DateTimeField(null=True, blank=True)
	sequence = models.JSONField(default=list, blank=True)  # list of ints shown
	response = models.JSONField(default=list, blank=True)  # list of ints entered
	num_correct = models.PositiveIntegerField(default=0)
	num_total = models.PositiveIntegerField(default=0)
	duration_seconds = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ["-started_at"]

	def __str__(self) -> str:
		return f"MemoryTest(user={self.user_id}, {self.num_correct}/{self.num_total})"


class ScenarioTestSession(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scenario_tests")
	started_at = models.DateTimeField(auto_now_add=True)
	ended_at = models.DateTimeField(null=True, blank=True)
	scenario_text = models.TextField()
	num_correct = models.PositiveIntegerField(default=0)
	num_total = models.PositiveIntegerField(default=0)
	duration_seconds = models.PositiveIntegerField(default=0)
	details = models.JSONField(default=list, blank=True)

	class Meta:
		ordering = ["-started_at"]

	def __str__(self) -> str:
		return f"ScenarioTest(user={self.user_id}, {self.num_correct}/{self.num_total})"


