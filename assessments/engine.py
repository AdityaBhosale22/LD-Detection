"""Question generation and scoring for the five skill tests.

Each test follows the same lifecycle, which keeps the API stateless:
  start(user)            -> creates a session row and stores the questions on it
  public(session)        -> what the client may see before answering (never the answers)
  score(session, data)   -> grades the submitted answers and fills in the session
  result(session)        -> the graded result shown after submission
"""
import random

from django.utils import timezone

from .models import (
	GrammarTestSession,
	MathTestSession,
	MemoryTestSession,
	ReadingTestSession,
	ScenarioTestSession,
)


class SubmissionError(ValueError):
	pass


def _to_int(value):
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def _nth(values, index):
	return values[index] if isinstance(values, list) and index < len(values) else None


def _shuffled(options):
	"""Return options in random order so the correct answer isn't always in the same slot."""
	return random.sample(options, k=len(options))


class BaseTest:
	model = None

	@classmethod
	def submit(cls, session, data: dict):
		if session.ended_at is not None:
			raise SubmissionError("This test has already been submitted.")
		cls.score(session, data)
		session.duration_seconds = int(max(0, (timezone.now() - session.started_at).total_seconds()))
		session.ended_at = timezone.now()
		session.save()
		return session

	@classmethod
	def result(cls, session) -> dict:
		return {
			"id": session.id,
			"completed": session.ended_at is not None,
			"num_correct": session.num_correct,
			"num_total": session.num_total,
			"duration_seconds": session.duration_seconds,
			"details": getattr(session, "details", []) if session.ended_at else [],
		}


class MathTest(BaseTest):
	"""Ten addition/subtraction questions with operands 0..20."""
	model = MathTestSession

	@staticmethod
	def start(user):
		questions = [
			{"a": random.randint(0, 20), "b": random.randint(0, 20), "op": random.choice(["+", "-"])}
			for _ in range(10)
		]
		return MathTestSession.objects.create(user=user, num_total=len(questions), details=questions)

	@staticmethod
	def public(session):
		return {"questions": [{"a": q["a"], "b": q["b"], "op": q["op"]} for q in session.details]}

	@staticmethod
	def score(session, data):
		answers = data.get("answers", [])
		details = []
		for i, q in enumerate(session.details):
			answer = q["a"] + q["b"] if q["op"] == "+" else q["a"] - q["b"]
			user_val = _to_int(_nth(answers, i))
			details.append({**q, "answer": answer, "user": user_val, "correct": user_val == answer})
		session.details = details
		session.num_correct = sum(d["correct"] for d in details)


GRAMMAR_BANK = [
	{"prompt": "She ___ to school every day.", "options": ["go", "goes", "going"], "answer": "goes"},
	{"prompt": "They ___ playing outside.", "options": ["is", "are", "am"], "answer": "are"},
	{"prompt": "He is ___ honest man.", "options": ["a", "an", "the"], "answer": "an"},
	{"prompt": "I ___ dinner when you called.", "options": ["cook", "was cooking", "cooks"], "answer": "was cooking"},
	{"prompt": "One child, two ___.", "options": ["childs", "children", "childes"], "answer": "children"},
]


class GrammarTest(BaseTest):
	"""Five multiple-choice grammar items in random order."""
	model = GrammarTestSession

	@staticmethod
	def start(user):
		items = [{**item, "options": _shuffled(item["options"])} for item in random.sample(GRAMMAR_BANK, k=len(GRAMMAR_BANK))]
		return GrammarTestSession.objects.create(user=user, num_total=len(items), details=items)

	@staticmethod
	def public(session):
		return {"questions": [{"prompt": d["prompt"], "options": d["options"]} for d in session.details]}

	@staticmethod
	def score(session, data):
		answers = data.get("answers", [])
		details = []
		for i, item in enumerate(session.details):
			user_val = _nth(answers, i)
			details.append({**item, "user": user_val, "correct": user_val == item["answer"]})
		session.details = details
		session.num_correct = sum(d["correct"] for d in details)


PASSAGES = [
	"The quick brown fox jumps over the lazy dog.",
	"Reading fluently helps you understand and learn new ideas faster.",
	"Students should practice every day to improve their skills.",
]


def tokenize(text: str):
	return "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text).split()


class ReadingTest(BaseTest):
	"""Read a passage aloud; the browser transcribes speech, we measure WPM and word accuracy."""
	model = ReadingTestSession

	@staticmethod
	def start(user):
		return ReadingTestSession.objects.create(user=user, passage=random.choice(PASSAGES))

	@staticmethod
	def public(session):
		return {"passage": session.passage}

	@staticmethod
	def score(session, data):
		transcript = str(data.get("transcript", "")).strip()
		if not transcript:
			raise SubmissionError("Transcript is empty.")
		reading_seconds = _to_int(data.get("reading_seconds"))
		if not reading_seconds or reading_seconds <= 0:
			reading_seconds = max(1, int((timezone.now() - session.started_at).total_seconds()))
		ref_tokens = tokenize(session.passage)
		hyp_tokens = tokenize(transcript)
		ref_set = set(ref_tokens)
		overlap = sum(1 for t in hyp_tokens if t in ref_set)
		session.transcript = transcript
		session.wpm = round(len(hyp_tokens) / (reading_seconds / 60.0), 1)
		session.accuracy = round(min(1.0, overlap / max(1, len(ref_tokens))), 2)
		session.details = {"reading_seconds": reading_seconds, "words_read": len(hyp_tokens), "words_matched": overlap}

	@classmethod
	def result(cls, session):
		return {
			"id": session.id,
			"completed": session.ended_at is not None,
			"passage": session.passage,
			"transcript": session.transcript,
			"wpm": session.wpm,
			"accuracy": session.accuracy,
			"duration_seconds": session.duration_seconds,
		}


class MemoryTest(BaseTest):
	"""Show six digits briefly, then ask the student to recall them in order."""
	model = MemoryTestSession

	@staticmethod
	def start(user):
		sequence = [random.randint(0, 9) for _ in range(6)]
		return MemoryTestSession.objects.create(user=user, sequence=sequence, num_total=len(sequence))

	@staticmethod
	def public(session):
		return {"sequence": session.sequence, "display_seconds": 5}

	@staticmethod
	def score(session, data):
		response = [v for v in (_to_int(x) for x in data.get("response", [])) if v is not None]
		session.response = response
		session.num_correct = sum(1 for a, b in zip(session.sequence, response) if a == b)

	@classmethod
	def result(cls, session):
		data = super().result(session)
		data["details"] = [
			{"target": t, "user": _nth(session.response, i), "correct": _nth(session.response, i) == t}
			for i, t in enumerate(session.sequence)
		] if session.ended_at else []
		return data


SCENARIOS = [
	{
		"text": "Riya forgot her homework again. The teacher asked her why, and she said her little brother was sick and she had to help. The teacher gave her an extra day.",
		"qa": [
			{"q": "Why did Riya forget her homework?", "options": ["She played games", "Her brother was sick", "She lost it"], "a": "Her brother was sick"},
			{"q": "What did the teacher do?", "options": ["Punished her", "Gave her an extra day", "Ignored it"], "a": "Gave her an extra day"},
		],
	},
	{
		"text": "Aman saw a puppy stuck behind a fence. He called a neighbor for help. Together they opened the gate and the puppy ran to its mother.",
		"qa": [
			{"q": "What problem did Aman see?", "options": ["A puppy was stuck", "A cat was in a tree", "He lost a toy"], "a": "A puppy was stuck"},
			{"q": "Who helped Aman?", "options": ["His teacher", "A neighbor", "A police officer"], "a": "A neighbor"},
		],
	},
]


class ScenarioTest(BaseTest):
	"""A short story followed by comprehension questions."""
	model = ScenarioTestSession

	@staticmethod
	def start(user):
		scenario = random.choice(SCENARIOS)
		qa = [{**item, "options": _shuffled(item["options"])} for item in scenario["qa"]]
		return ScenarioTestSession.objects.create(
			user=user, scenario_text=scenario["text"], num_total=len(qa), details=qa
		)

	@staticmethod
	def public(session):
		return {
			"text": session.scenario_text,
			"questions": [{"prompt": d["q"], "options": d["options"]} for d in session.details],
		}

	@staticmethod
	def score(session, data):
		answers = data.get("answers", [])
		details = []
		for i, item in enumerate(session.details):
			user_val = _nth(answers, i)
			details.append({**item, "user": user_val, "correct": user_val == item["a"]})
		session.details = details
		session.num_correct = sum(d["correct"] for d in details)


TESTS = {
	"math": MathTest,
	"grammar": GrammarTest,
	"reading": ReadingTest,
	"memory": MemoryTest,
	"scenario": ScenarioTest,
}
