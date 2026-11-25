from __future__ import annotations

from dataclasses import dataclass
from typing import List

from django.db.models import Avg

from assessments.models import MathTestSession, GrammarTestSession, ReadingTestSession, MemoryTestSession, ScenarioTestSession
from .models import Recommendation


@dataclass
class AreaScore:
	area: str
	score: float  # 0..1 weakness (higher = weaker)


def compute_user_area_scores(user) -> List[AreaScore]:
	"""Weakness score per area (0 = strong, 1 = weak), averaged over completed tests.

	Areas the user has not completed a test for are left out rather than scored as 0.
	"""
	areas: List[AreaScore] = []

	def completed(model):
		return model.objects.filter(user=user, ended_at__isnull=False)

	def add_ratio(area, model):
		agg = completed(model).aggregate(avg_correct=Avg("num_correct"), avg_total=Avg("num_total"))
		if agg["avg_total"]:
			areas.append(AreaScore(area, 1.0 - agg["avg_correct"] / agg["avg_total"]))

	add_ratio("math", MathTestSession)
	add_ratio("grammar", GrammarTestSession)
	# Reading weakness: combine low accuracy and low WPM
	read = completed(ReadingTestSession).aggregate(acc=Avg("accuracy"), wpm=Avg("wpm"))
	if read["acc"] is not None:
		acc_weak = 1.0 - read["acc"]
		wpm_weak = 1.0 if read["wpm"] < 80 else (0.5 if read["wpm"] < 120 else 0.0)
		areas.append(AreaScore("reading", min(1.0, max(0.0, 0.6 * acc_weak + 0.4 * wpm_weak))))
	add_ratio("memory", MemoryTestSession)
	add_ratio("scenario", ScenarioTestSession)
	return areas


def generate_recommendations(user) -> List[Recommendation]:
	areas = compute_user_area_scores(user)
	Recommendation.objects.filter(user=user).delete()
	created: List[Recommendation] = []
	for a in areas:
		if a.score <= 0.1:
			continue
		if a.area == "math":
			created.append(Recommendation.objects.create(
				user=user,
				area="math",
				title="Basic numeracy practice",
				description="Practice addition and subtraction within 20. Focus on accuracy, then speed.",
				url="https://www.khanacademy.org/math/arithmetic",
				score=a.score,
			))
		elif a.area == "grammar":
			created.append(Recommendation.objects.create(
				user=user,
				area="grammar",
				title="Subject-verb agreement drills",
				description="Short exercises on articles and agreement.",
				url="https://www.ego4u.com/en/cram-up/grammar",
				score=a.score,
			))
		elif a.area == "reading":
			created.append(Recommendation.objects.create(
				user=user,
				area="reading",
				title="Fluency passages (timed)",
				description="Read graded passages aloud daily; track WPM and accuracy.",
				url="https://readtheory.org/",
				score=a.score,
			))
		elif a.area == "memory":
			created.append(Recommendation.objects.create(
				user=user,
				area="memory",
				title="Working memory games",
				description="Sequence recall and matching games to build memory span.",
				url="https://www.cogniFit.com/",
				score=a.score,
			))
		elif a.area == "scenario":
			created.append(Recommendation.objects.create(
				user=user,
				area="scenario",
				title="Reading comprehension practice",
				description="Answer wh- questions after short stories to improve inference.",
				url="https://www.ixl.com/ela/",
				score=a.score,
			))
	return created


