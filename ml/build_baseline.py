from pathlib import Path
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression


def main() -> None:
	# Feature order must match predictions.services.default_model_spec
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

	# Create synthetic training data
	# Intuition: reading difficulties and low attention increase LD risk; age, gender neutral here
	n_samples = 1000
	age = np.random.randint(6, 19, size=(n_samples, 1)).astype(float)
	gender_idx = np.random.randint(0, 3, size=n_samples)
	gender = np.eye(3, dtype=float)[gender_idx]
	reading = np.random.binomial(1, 0.3, size=(n_samples, 1)).astype(float)
	attention_idx = np.random.randint(0, 3, size=n_samples)
	attention_levels = np.eye(3, dtype=float)[attention_idx]

	X = np.concatenate([age, gender, reading := reading, attention_levels], axis=1)

	# Generate probabilities using a simple linear combination
	logits = (
		0.0
		+ 0.05 * (X[:, 0] - 10.0)  # slight age effect
		+ 1.5 * X[:, 4]            # reading_difficulties
		+ 0.8 * X[:, 5]            # attention_low
		- 0.5 * X[:, 7]            # attention_high
	)
	p = 1.0 / (1.0 + np.exp(-logits))
	Y = (np.random.rand(n_samples) < p).astype(int)

	model = LogisticRegression(max_iter=1000)
	model.fit(X, Y)

	# Save model next to this script
	out_path = Path(__file__).resolve().parent / "ld_model.joblib"
	joblib.dump(model, out_path)
	print(f"Saved baseline model to: {out_path}")


if __name__ == "__main__":
	main()


