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
	areas: List[AreaScore] = []
	# For each area, compute average performance and convert to weakness score
	def ratio(qs, correct_field="num_correct", total_field="num_total"):
		agg = qs.aggregate(avg_correct=Avg(correct_field), avg_total=Avg(total_field))
		c = (agg["avg_correct"] or 0)
		t = (agg["avg_total"] or 0)
		return (1.0 - (c / t)) if t else 0.0

	areas.append(AreaScore("math", ratio(MathTestSession.objects.filter(user=user))))
	areas.append(AreaScore("grammar", ratio(GrammarTestSession.objects.filter(user=user))))
	# Reading weakness: combine low accuracy and low WPM
	read_qs = ReadingTestSession.objects.filter(user=user)
	read_acc_weak = 1.0 - (read_qs.aggregate(v=Avg("accuracy"))["v"] or 0)
	read_wpm = (read_qs.aggregate(v=Avg("wpm"))["v"] or 0)
	read_wpm_weak = 1.0 if read_wpm < 80 else (0.5 if read_wpm < 120 else 0.0)
	areas.append(AreaScore("reading", min(1.0, max(0.0, 0.6 * read_acc_weak + 0.4 * read_wpm_weak))))
	areas.append(AreaScore("memory", ratio(MemoryTestSession.objects.filter(user=user))))
	areas.append(AreaScore("scenario", ratio(ScenarioTestSession.objects.filter(user=user))))
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


