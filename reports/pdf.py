"""Builds the downloadable student PDF report (ReportLab + a Matplotlib chart)."""
from io import BytesIO
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")  # headless backend, no display needed in the container
import matplotlib.pyplot as plt  # noqa: E402
from django.utils import timezone  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet  # noqa: E402
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

from assessments.models import (  # noqa: E402
	DemographicProfile,
	GrammarTestSession,
	MathTestSession,
	MemoryTestSession,
	ReadingTestSession,
	ScenarioTestSession,
)
from predictions.models import PredictionResult  # noqa: E402
from recommendations.models import Recommendation  # noqa: E402
from recommendations.services import compute_user_area_scores  # noqa: E402

TABLE_STYLE = TableStyle([
	("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
	("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
])


def _yes_no(value) -> str:
	return "Yes" if value else "No"


def _latest_completed(model, user):
	return model.objects.filter(user=user, ended_at__isnull=False).order_by("-started_at").first()


def build_report_pdf(user) -> bytes:
	styles = getSampleStyleSheet()
	story = []

	def para(text, style="Normal"):
		story.append(Paragraph(text, styles[style]))

	def table(rows):
		t = Table(rows, hAlign="LEFT")
		t.setStyle(TABLE_STYLE)
		story.append(t)

	para("LD Detection - Student Report", "Title")
	para(timezone.now().strftime("Generated on %Y-%m-%d %H:%M UTC"))
	para("This is a screening aid, not a medical diagnosis.")
	story.append(Spacer(1, 12))

	# Profile
	para(f"Student: {escape(user.email)}", "Heading3")
	profile = DemographicProfile.objects.filter(user=user).first()
	if profile:
		table([
			["Age", profile.age],
			["Gender", profile.get_gender_display()],
			["Reading difficulties", _yes_no(profile.reading_difficulties)],
			["Attention span", profile.get_attention_span_display()],
		])
	story.append(Spacer(1, 12))

	# Prediction
	para("Model Prediction", "Heading3")
	prediction = PredictionResult.objects.filter(user=user).first()
	if prediction:
		para(f"Result: <b>{escape(prediction.label)}</b>")
		para(f"Probability of LD indicators: {prediction.probability:.0%}")
	else:
		para("No prediction yet.")
	story.append(Spacer(1, 12))

	# Test sections
	def test_section(title, model, header, rows_fn):
		para(title, "Heading3")
		session = _latest_completed(model, user)
		if session is None:
			para("Not completed yet.")
		else:
			para(f"Score: {session.num_correct} / {session.num_total} in {session.duration_seconds} seconds")
			table([header] + rows_fn(session))
		story.append(Spacer(1, 12))

	test_section(
		"Math", MathTestSession, ["#", "Question", "Answer given", "Correct answer", "Correct?"],
		lambda s: [[i + 1, f"{d['a']} {d['op']} {d['b']}", d.get("user"), d.get("answer"), _yes_no(d.get("correct"))]
		           for i, d in enumerate(s.details)],
	)
	test_section(
		"Grammar", GrammarTestSession, ["#", "Prompt", "Answer given", "Correct answer", "Correct?"],
		lambda s: [[i + 1, d.get("prompt"), d.get("user"), d.get("answer"), _yes_no(d.get("correct"))]
		           for i, d in enumerate(s.details)],
	)

	para("Reading", "Heading3")
	reading = _latest_completed(ReadingTestSession, user)
	if reading:
		para(f"Speed: {reading.wpm:.0f} words per minute, word accuracy: {reading.accuracy:.0%}")
		para(f"Passage: {escape(reading.passage)}")
		para(f"Transcript: {escape(reading.transcript)}")
	else:
		para("Not completed yet.")
	story.append(Spacer(1, 12))

	test_section(
		"Memory", MemoryTestSession, ["#", "Shown", "Recalled", "Correct?"],
		lambda s: [[i + 1, t, s.response[i] if i < len(s.response) else "-",
		            _yes_no(i < len(s.response) and s.response[i] == t)]
		           for i, t in enumerate(s.sequence)],
	)
	test_section(
		"Comprehension", ScenarioTestSession, ["#", "Question", "Answer given", "Correct answer", "Correct?"],
		lambda s: [[i + 1, d.get("q"), d.get("user"), d.get("a"), _yes_no(d.get("correct"))]
		           for i, d in enumerate(s.details)],
	)

	# Area chart
	areas = compute_user_area_scores(user)
	if areas:
		para("Weakness by Area", "Heading3")
		fig, ax = plt.subplots(figsize=(6, 3))
		ax.bar([a.area.title() for a in areas], [a.score for a in areas], color="#2563eb")
		ax.set_ylim(0, 1)
		ax.set_ylabel("Weakness (0 = strong, 1 = weak)")
		fig.tight_layout()
		img = BytesIO()
		fig.savefig(img, format="png", dpi=150)
		plt.close(fig)
		img.seek(0)
		story.append(Image(img, width=400, height=200))
		story.append(Spacer(1, 12))

	# Recommendations
	para("Recommendations", "Heading3")
	recs = Recommendation.objects.filter(user=user).order_by("-score")[:10]
	if recs:
		table([["Area", "Suggestion", "Weakness"]] + [[r.get_area_display(), r.title, f"{r.score:.2f}"] for r in recs])
	else:
		para("No recommendations at this time.")

	buffer = BytesIO()
	SimpleDocTemplate(buffer, pagesize=A4, title="LD Detection Report").build(story)
	return buffer.getvalue()
