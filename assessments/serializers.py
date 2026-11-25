from rest_framework import serializers

from .models import DemographicProfile


class DemographicProfileSerializer(serializers.ModelSerializer):
	class Meta:
		model = DemographicProfile
		fields = [
			"id",
			"age",
			"gender",
			"academic_history",
			"reading_difficulties",
			"attention_span",
			"learning_issues_notes",
			"created_at",
		]
		read_only_fields = ["id", "created_at"]

	def validate_age(self, age):
		if age < 4 or age > 25:
			raise serializers.ValidationError("Please enter an age between 4 and 25.")
		return age
