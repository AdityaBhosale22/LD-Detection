from django import forms
from .models import DemographicProfile


class DemographicProfileForm(forms.ModelForm):
	class Meta:
		model = DemographicProfile
		fields = [
			"age",
			"gender",
			"academic_history",
			"reading_difficulties",
			"attention_span",
			"learning_issues_notes",
		]

	def clean_age(self):
		age = self.cleaned_data.get("age")
		if age is None or age <= 0 or age > 25:
			raise forms.ValidationError("Please enter a valid age between 1 and 25.")
		return age


