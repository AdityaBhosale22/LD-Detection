from io import BytesIO
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from assessments.models import (
	DemographicProfile,
	MathTestSession,
	GrammarTestSession,
	ReadingTestSession,
	MemoryTestSession,
	ScenarioTestSession,
)
from predictions.models import PredictionResult
from recommendations.models import Recommendation


@login_required
def download_report(request):
	buffer = BytesIO()
	doc = SimpleDocTemplate(buffer, pagesize=A4)
	styles = getSampleStyleSheet()
	story = []

	# Header
	story.append(Paragraph("LD Detection - Student Report", styles["Title"]))
	story.append(Paragraph(datetime.utcnow().strftime("Generated on %Y-%m-%d %H:%M UTC"), styles["Normal"]))
	story.append(Spacer(1, 12))

	# User info
	story.append(Paragraph(f"User: {request.user.email}", styles["Heading3"]))
	profile = DemographicProfile.objects.filter(user=request.user).order_by("-created_at").first()
	if profile:
		data = [["Age", profile.age], ["Gender", profile.gender], ["Reading difficulties", "Yes" if profile.reading_difficulties else "No"], ["Attention", profile.attention_span]]
		table = Table(data, hAlign="LEFT")
		table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.25, colors.grey)]))
		story.append(table)
		story.append(Spacer(1, 12))

	# Prediction
	story.append(Paragraph("Model Prediction", styles["Heading3"]))
	pred = PredictionResult.objects.filter(user=request.user).order_by("-created_at").first()
	if pred:
		story.append(Paragraph(f"Label: <b>{pred.label}</b>", styles["Normal"]))
		story.append(Paragraph(f"Probability (LD): {pred.probability:.2f}", styles["Normal"]))
	else:
		story.append(Paragraph("No prediction available.", styles["Normal"]))
	story.append(Spacer(1, 12))

	# Test summaries
	def add_test_section(title, qs, cols, row_fn):
		story.append(Paragraph(title, styles["Heading3"]))
		latest = qs.order_by("-started_at").first()
		if latest:
			story.append(Paragraph(f"Score: {getattr(latest, 'num_correct', 0)} / {getattr(latest, 'num_total', 0)}", styles["Normal"]))
			story.append(Paragraph(f"Duration: {getattr(latest, 'duration_seconds', 0)} seconds", styles["Normal"]))
			rows = [cols] + row_fn(latest)
			t = Table(rows, hAlign="LEFT")
			t.setStyle(TableStyle([
				("GRID", (0,0), (-1,-1), 0.25, colors.grey),
				("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
			]))
			story.append(t)
		else:
			story.append(Paragraph("No attempts recorded.", styles["Normal"]))
		story.append(Spacer(1, 12))

	add_test_section(
		"Math Test",
		MathTestSession.objects.filter(user=request.user),
		["#", "Question", "Your", "Correct", "✓"],
		lambda s: [[i+1, f"{d['a']} {d['op']} {d['b']}", d.get("user"), d.get("answer"), "Yes" if d.get("correct") else "No"] for i,d in enumerate(s.details[:10])]
	)

	add_test_section(
		"Grammar Test",
		GrammarTestSession.objects.filter(user=request.user),
		["#", "Prompt", "Your", "Correct", "✓"],
		lambda s: [[i+1, d.get("prompt"), d.get("user"), d.get("answer"), "Yes" if d.get("correct") else "No"] for i,d in enumerate(s.details[:10])]
	)

	# Reading summary
	story.append(Paragraph("Reading Test", styles["Heading3"]))
	read = ReadingTestSession.objects.filter(user=request.user).order_by("-started_at").first()
	if read:
		story.append(Paragraph(f"WPM: {read.wpm:.1f}, Accuracy: {read.accuracy:.2f}", styles["Normal"]))
		story.append(Paragraph("Passage:", styles["Normal"]))
		story.append(Paragraph(read.passage, styles["Normal"]))
	else:
		story.append(Paragraph("No attempts recorded.", styles["Normal"]))
	story.append(Spacer(1, 12))

	add_test_section(
		"Memory Test",
		MemoryTestSession.objects.filter(user=request.user),
		["#", "Target", "Your", "✓"],
		lambda s: [[i+1, s.sequence[i] if i < len(s.sequence) else "", s.response[i] if i < len(s.response) else "", "Yes" if (i < len(s.sequence) and i < len(s.response) and s.sequence[i]==s.response[i]) else "No"] for i in range(min(10, max(len(s.sequence), len(s.response))))]
	)

	add_test_section(
		"Scenario Test",
		ScenarioTestSession.objects.filter(user=request.user),
		["#", "Question", "Your", "Correct", "✓"],
		lambda s: [[i+1, d.get("q"), d.get("user"), d.get("a"), "Yes" if d.get("correct") else "No"] for i,d in enumerate(s.details[:10])]
	)

	# Recommendations
	story.append(Paragraph("Recommendations", styles["Heading3"]))
	recs = Recommendation.objects.filter(user=request.user).order_by("-score")[:10]
	if recs:
		rows = [["Area", "Title", "Score"]] + [[r.area.title(), r.title, f"{r.score:.2f}"] for r in recs]
		t = Table(rows, hAlign="LEFT")
		t.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.25, colors.grey), ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke)]))
		story.append(t)
	else:
		story.append(Paragraph("No recommendations at this time.", styles["Normal"]))

	doc.build(story)
	pdf = buffer.getvalue()
	buffer.close()
	resp = HttpResponse(pdf, content_type="application/pdf")
	resp["Content-Disposition"] = "attachment; filename=ld_report.pdf"
	return resp


