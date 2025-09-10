from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
import random

from .forms import DemographicProfileForm
from .models import DemographicProfile, MathTestSession


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


