from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
import random
import math

from .forms import DemographicProfileForm
from .models import DemographicProfile, MathTestSession, GrammarTestSession, ReadingTestSession


@login_required
def demographic_intake(request):
	if request.method == "POST":
		form = DemographicProfileForm(request.POST)
		if form.is_valid():
			profile: DemographicProfile = form.save(commit=False)
			profile.user = request.user
			profile.save()
			return redirect(reverse("intake_success"))
	else:
		form = DemographicProfileForm()
	return render(request, "assessments/demographic_intake.html", {"form": form})


@login_required
def intake_success(_request):
	return render(_request, "assessments/intake_success.html")


@login_required
def math_test_start(request):
	# Generate 10 random arithmetic questions (+ or - within 0..20)
	questions = []
	for _ in range(10):
		a = random.randint(0, 20)
		b = random.randint(0, 20)
		op = random.choice(["+", "-"])
		questions.append({"a": a, "b": b, "op": op})
	# Create session scaffold
	session = MathTestSession.objects.create(user=request.user, num_total=len(questions))
	request.session["math_test_id"] = session.id
	request.session["math_questions"] = questions
	request.session["math_start_ts"] = timezone.now().timestamp()
	return render(request, "assessments/math_test.html", {"questions": questions, "session": session})


@login_required
def math_test_submit(request):
	if request.method != "POST":
		return redirect("math_test_start")
	session_id = request.session.get("math_test_id")
	questions = request.session.get("math_questions", [])
	start_ts = request.session.get("math_start_ts")
	if not session_id or not questions or not start_ts:
		return redirect("math_test_start")
	session = MathTestSession.objects.get(id=session_id, user=request.user)
	correct = 0
	details = []
	for idx, q in enumerate(questions):
		a, b, op = q["a"], q["b"], q["op"]
		answer = a + b if op == "+" else a - b
		user_key = f"q_{idx}"
		try:
			user_val = int(request.POST.get(user_key, ""))
		except ValueError:
			user_val = None
		is_correct = user_val == answer
		if is_correct:
			correct += 1
		details.append({"a": a, "b": b, "op": op, "answer": answer, "user": user_val, "correct": is_correct})
	duration = int(max(0, timezone.now().timestamp() - start_ts))
	session.num_correct = correct
	session.duration_seconds = duration
	session.details = details
	session.ended_at = timezone.now()
	session.save()
	# Clear session keys
	for k in ["math_test_id", "math_questions", "math_start_ts"]:
		request.session.pop(k, None)
	return redirect("math_test_result", session_id=session.id)


@login_required
def math_test_result(request, session_id: int):
	session = MathTestSession.objects.get(id=session_id, user=request.user)
	return render(request, "assessments/math_test_result.html", {"session": session})


@login_required
def grammar_test_start(request):
	# Five MCQ grammar items
	bank = [
		{"prompt": "Choose the correct form: She __ to school every day.", "options": ["go", "goes", "going"], "answer": "goes"},
		{"prompt": "Fill the blank: They ___ playing.", "options": ["is", "are", "am"], "answer": "are"},
		{"prompt": "Correct article: He is ___ honest man.", "options": ["a", "an", "the"], "answer": "an"},
		{"prompt": "Verb tense: I ___ dinner when you called.", "options": ["cook", "was cooking", "cooks"], "answer": "was cooking"},
		{"prompt": "Plural form: One child, two ___.", "options": ["childs", "children", "childes"], "answer": "children"},
	]
	random.shuffle(bank)
	items = bank[:5]
	session = GrammarTestSession.objects.create(user=request.user, num_total=len(items))
	request.session["grammar_test_id"] = session.id
	request.session["grammar_items"] = items
	request.session["grammar_start_ts"] = timezone.now().timestamp()
	return render(request, "assessments/grammar_test.html", {"items": items, "session": session})


@login_required
def grammar_test_submit(request):
	if request.method != "POST":
		return redirect("grammar_test_start")
	session_id = request.session.get("grammar_test_id")
	items = request.session.get("grammar_items", [])
	start_ts = request.session.get("grammar_start_ts")
	if not session_id or not items or not start_ts:
		return redirect("grammar_test_start")
	session = GrammarTestSession.objects.get(id=session_id, user=request.user)
	correct = 0
	details = []
	for idx, item in enumerate(items):
		key = f"q_{idx}"
		user_val = request.POST.get(key)
		is_correct = user_val == item["answer"]
		if is_correct:
			correct += 1
		details.append({
			"prompt": item["prompt"],
			"options": item["options"],
			"answer": item["answer"],
			"user": user_val,
			"correct": is_correct,
		})
	duration = int(max(0, timezone.now().timestamp() - start_ts))
	session.num_correct = correct
	session.duration_seconds = duration
	session.details = details
	session.ended_at = timezone.now()
	session.save()
	for k in ["grammar_test_id", "grammar_items", "grammar_start_ts"]:
		request.session.pop(k, None)
	return redirect("grammar_test_result", session_id=session.id)


@login_required
def grammar_test_result(request, session_id: int):
	session = GrammarTestSession.objects.get(id=session_id, user=request.user)
	return render(request, "assessments/grammar_test_result.html", {"session": session})


# Reading test
_PASSAGES = [
	"The quick brown fox jumps over the lazy dog.",
	"Reading fluently helps you understand and learn new ideas faster.",
	"Students should practice every day to improve their skills.",
]


def _tokenize(text: str):
	return [t for t in ''.join(c.lower() if c.isalnum() or c.isspace() else ' ' for c in text).split() if t]


@login_required
def reading_test_start(request):
	passage = random.choice(_PASSAGES)
	session = ReadingTestSession.objects.create(user=request.user, passage=passage)
	request.session["reading_test_id"] = session.id
	request.session["reading_start_ts"] = timezone.now().timestamp()
	return render(request, "assessments/reading_test.html", {"session": session, "passage": passage})


@login_required
def reading_test_submit(request):
	if request.method != "POST":
		return redirect("reading_test_start")
	session_id = request.session.get("reading_test_id")
	start_ts = request.session.get("reading_start_ts")
	if not session_id or not start_ts:
		return redirect("reading_test_start")
	session = ReadingTestSession.objects.get(id=session_id, user=request.user)
	transcript = request.POST.get("transcript", "").strip()
	duration = int(max(0, timezone.now().timestamp() - start_ts))
	# Compute WPM and accuracy
	ref_tokens = _tokenize(session.passage)
	hyp_tokens = _tokenize(transcript)
	wpm = (len(hyp_tokens) / (duration / 60.0)) if duration > 0 else 0.0
	# simple overlap accuracy
	ref_set = set(ref_tokens)
	overlap = sum(1 for t in hyp_tokens if t in ref_set)
	accuracy = (overlap / max(1, len(ref_tokens)))
	session.transcript = transcript
	session.duration_seconds = duration
	session.wpm = float(f"{wpm:.2f}")
	session.accuracy = float(f"{accuracy:.2f}")
	session.details = {"ref_len": len(ref_tokens), "hyp_len": len(hyp_tokens), "overlap": overlap}
	session.ended_at = timezone.now()
	session.save()
	for k in ["reading_test_id", "reading_start_ts"]:
		request.session.pop(k, None)
	return redirect("reading_test_result", session_id=session.id)


@login_required
def reading_test_result(request, session_id: int):
	session = ReadingTestSession.objects.get(id=session_id, user=request.user)
	return render(request, "assessments/reading_test_result.html", {"session": session})


