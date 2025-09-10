from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np

from assessments.models import DemographicProfile


@dataclass
class ModelSpec:
	path: Path
	feature_order: List[str]
	positive_label: str = "LD Detected"
	negative_label: str = "No LD Detected"


class LDClassifier:
	def __init__(self, spec: ModelSpec):
		self.spec = spec
		self._model = None

	def load(self) -> None:
		if self._model is None:
			self._model = joblib.load(self.spec.path)

	def _vectorize(self, profile: DemographicProfile) -> np.ndarray:
		values: Dict[str, Any] = {
			"age": profile.age,
			"gender_male": 1 if profile.gender == "male" else 0,
			"gender_female": 1 if profile.gender == "female" else 0,
			"gender_other": 1 if profile.gender == "other" else 0,
			"reading_difficulties": int(profile.reading_difficulties),
			"attention_low": 1 if profile.attention_span == "low" else 0,
			"attention_medium": 1 if profile.attention_span == "medium" else 0,
			"attention_high": 1 if profile.attention_span == "high" else 0,
		}
		return np.array([[values.get(name, 0) for name in self.spec.feature_order]], dtype=float)

	def predict(self, profile: DemographicProfile) -> Dict[str, Any]:
		self.load()
		X = self._vectorize(profile)
		proba = getattr(self._model, "predict_proba", None)
		if proba is not None:
			probs = proba(X)[0]
			p_ld = float(probs[1]) if len(probs) > 1 else float(probs[0])
		else:
			# Fallback for models without predict_proba
			pred = self._model.predict(X)[0]
			p_ld = float(pred)
		label = self.spec.positive_label if p_ld >= 0.5 else self.spec.negative_label
		return {"label": label, "probability": p_ld}


def default_model_spec() -> ModelSpec:
	base = Path(__file__).resolve().parent.parent / "ml"
	path = base / "ld_model.joblib"
	# Keep in sync with training pipeline
	feature_order = [
		"age",
		"gender_male",
		"gender_female",
		"gender_other",
		"reading_difficulties",
		"attention_low",
		"attention_medium",
		"attention_high",
	]
	return ModelSpec(path=path, feature_order=feature_order)


