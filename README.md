# LD Detection

![CI](https://github.com/AdityaBhosale22/LD-Detection/actions/workflows/ci.yml/badge.svg)

**Live demo:** _add your Vercel URL here_ · The API sleeps when idle, so the first sign-in can take ~30–60s.

A web app that screens students for possible learning difficulties (LD). Students fill in a
short profile and take five quick skill tests. A machine-learning model gives a screening
result, a dashboard shows weak areas, and the app suggests practice resources and generates a
downloadable PDF report.

- **Frontend:** React + TypeScript (Vite, Tailwind), deployed on **Vercel**
- **Backend:** Django REST API with token auth, containerised with **Docker**
- **CI/CD:** **GitHub Actions** (tests, lint, Docker smoke test) and a **Jenkins** pipeline that pushes to **AWS ECR** and deploys to **EC2**
- **Cloud:** API on Render (live demo) or EC2, PostgreSQL (Neon), PDF reports archived to **S3**

## Features

- **Accounts:** register and sign in with email, with student, parent and teacher roles
- **Five assessments:**
  - **Math:** 10 arithmetic questions
  - **Grammar:** multiple choice
  - **Reading aloud:** speech recognition in the browser, scored on words per minute and accuracy
  - **Memory:** recall a digit sequence
  - **Comprehension:** a short story with questions
- **Screening:** a scikit-learn model gives the probability of LD indicators from the student profile
- **Dashboard:** progress, latest scores and performance by area
- **Recommendations:** practice resources for the weakest areas
- **PDF report:** ReportLab + a Matplotlib chart, uploaded to S3 when it is configured

## Architecture

```
            ┌─────────────── Vercel ───────────────┐
 Browser ──▶│ React SPA (frontend/)                │
            └──────────────────┬───────────────────┘
                               │ HTTPS, Authorization: Token …
            ┌──────────────────▼───────────────────┐
            │ Django REST API in Docker (gunicorn) │──▶ S3 (PDF reports)
            │ Render (demo)  or  EC2 via Jenkins   │
            └──────────────────┬───────────────────┘
                               ▼
                        PostgreSQL (Neon / container)

 git push ─▶ GitHub Actions: backend tests on Postgres · frontend lint+build · docker compose smoke test
 main     ─▶ Jenkins: build image → test in image → push to ECR → deploy to EC2 → health check
```

## API overview

All endpoints except register and login need an `Authorization: Token <key>` header.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register/`, `/api/auth/login/` | Returns `{token, user}` |
| POST / GET | `/api/auth/logout/`, `/api/auth/me/` | End the session / current user |
| GET / POST | `/api/intake/` | Latest profile / save a new one |
| GET / POST | `/api/predictions/` | Latest prediction / run the model |
| POST | `/api/tests/<kind>/start/` | Start a test (`math`, `grammar`, `reading`, `memory`, `scenario`) |
| POST | `/api/tests/<kind>/<id>/submit/` | Submit answers and get the graded result |
| GET | `/api/tests/<kind>/<id>/` | Result of a test |
| GET | `/api/dashboard/` | Everything the dashboard needs in one call |
| GET | `/api/recommendations/` | Practice suggestions, weakest area first |
| GET | `/api/report/` | PDF report (also archived to S3) |
| GET | `/healthz/` | Health check (also tests the database) |

The tests are stateless. Questions are stored on the test session when it starts, answers are
never sent to the browser, and a test can only be submitted once.

## Run locally

**Backend (Python 3.12):**

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ml/build_baseline.py        # trains ml/ld_model.joblib
python manage.py migrate
python manage.py runserver         # http://localhost:8000
```

Or run the API + PostgreSQL in Docker with `docker compose up --build`.

**Frontend (Node 22+):**

```bash
cd frontend
cp .env.example .env               # VITE_API_URL=http://localhost:8000
npm install
npm run dev                        # http://localhost:5173
```

## Tests and checks

```bash
python manage.py test tests                  # 19 API tests
cd frontend && npm run lint && npm run build # ESLint + TypeScript + production build
```

The backend tests cover:
- auth (tokens, weak passwords, logout)
- the profile-to-prediction flow
- scoring for all five tests, including that answers are hidden and a test can't be submitted twice
- users being unable to see each other's data
- dashboard and recommendations
- the PDF report and the S3 upload (boto3 mocked)
- CORS

## Deployment

- **Live demo (Vercel + Render + Neon):** [`deploy/LIVE_DEPLOY.md`](deploy/LIVE_DEPLOY.md)
- **AWS (Jenkins → ECR → EC2, S3, IAM role):** [`deploy/AWS_DEPLOY.md`](deploy/AWS_DEPLOY.md)

Both deploy the same `Dockerfile`. Configuration comes only from environment variables:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Required when `DJANGO_DEBUG=0` |
| `DJANGO_DEBUG` | `1` locally (default), `0` in Docker/production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames |
| `DATABASE_URL` | PostgreSQL URL (defaults to SQLite) |
| `CORS_ALLOWED_ORIGINS` | Frontend URL(s) allowed to call the API |
| `AWS_REGION`, `AWS_S3_REPORTS_BUCKET` | Enable the S3 report archive |
| `VITE_API_URL` (frontend) | API base URL |

## About the ML model

`ml/build_baseline.py` trains a logistic regression on **synthetic data**: reading
difficulties and low attention raise the risk. It demonstrates the full pipeline
(features → model → stored prediction → report). It is not a clinically validated tool, and
the app says so wherever it shows a result. The next step would be to train on real
assessment data and use the test scores as features.

## Project structure

```
frontend/          React + TypeScript app (Vercel)
accounts/          email-based user model, token auth endpoints
assessments/       profile endpoint + test engine (question generation and scoring)
predictions/       model loading and inference
recommendations/   weakness scoring and practice suggestions
reports/           dashboard summary, PDF report, S3 upload
ml/                baseline model training script
lddiag/            Django settings, URLs, /healthz/
tests/             API test suite
docker/, Dockerfile, docker-compose.yml, Jenkinsfile, render.yaml, .github/workflows/
deploy/            deployment guides
```
