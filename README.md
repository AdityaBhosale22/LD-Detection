# LD Detection

![CI](https://github.com/AdityaBhosale22/LD-Detection/actions/workflows/ci.yml/badge.svg)

A Django web app that screens students for possible learning disabilities (LD). Students
complete a short intake and five skill tests. The app then runs an ML model on their profile,
shows weak areas on a dashboard, suggests practice resources, and generates a downloadable PDF
report. Reports are archived to Amazon S3.

The app is containerised with Docker, tested in GitHub Actions, and deployed to AWS EC2
through a Jenkins pipeline that pushes images to Amazon ECR.

## Features

- **Accounts:** email-based registration and login with student, teacher and parent roles
- **Assessments:** demographic intake plus math, grammar, reading, memory and scenario tests, with scoring and timing
- **Prediction:** a scikit-learn logistic regression model gives the probability of LD from the intake profile
- **Recommendations:** per-area weakness scores mapped to practice resources
- **Reports:** a PDF report (ReportLab + Matplotlib chart) that is downloaded and also uploaded to S3
- **Health check:** `/healthz/` checks the database and is used by Docker, CI and the deploy step

## Tech stack

| Layer      | Tools                                               |
|------------|-----------------------------------------------------|
| App        | Python 3.12, Django 5, scikit-learn, ReportLab, Matplotlib |
| Database   | PostgreSQL 16 (Docker/production), SQLite (local dev) |
| Container  | Docker, Docker Compose, gunicorn, WhiteNoise        |
| CI         | GitHub Actions (tests on Postgres, Docker build, smoke test) |
| CD         | Jenkins: build → test → push to ECR → deploy to EC2 |
| Cloud      | AWS EC2, ECR, S3, IAM instance role                 |

## Architecture

```
                 ┌──────────────── GitHub ────────────────┐
  git push ────▶ │  GitHub Actions: tests + docker build  │
                 └───────────────────┬────────────────────┘
                                     │
                              Jenkins pipeline
                 build image → run tests → push to ECR → ssh deploy
                                     │
                    ┌────────────── EC2 ───────────────┐
                    │  docker compose                  │
                    │   ├─ web: Django + gunicorn :80  │──▶ S3 (PDF reports)
                    │   └─ db:  PostgreSQL 16          │
                    └──────────────────────────────────┘
```

## Run locally

### Option 1: Docker (recommended)

```bash
cp .env.example .env        # optional; sensible defaults are built in
docker compose up --build
```

Then open <http://localhost:8000> and register a new account.

### Option 2: Python virtualenv

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ml/build_baseline.py        # trains ml/ld_model.joblib
python manage.py migrate
python manage.py runserver
```

## Tests

```bash
python manage.py test tests
```

The tests cover registration and login protection, the intake-to-prediction flow (including
blocking access to another user's data), math test scoring, PDF generation, and the S3 upload
(boto3 is mocked, so no AWS account is needed).

## CI/CD

**GitHub Actions** (`.github/workflows/ci.yml`) runs on every push and pull request:
1. Runs the test suite against a PostgreSQL service container
2. Fails if model changes are missing a migration
3. Builds the Docker image, starts the full `docker compose` stack and polls `/healthz/`

**Jenkins** (`Jenkinsfile`) handles delivery on `main`:
1. Builds the Docker image, tagged with the build number
2. Runs the tests inside that image
3. Pushes the image to Amazon ECR
4. SSHes into EC2, pulls the new image and restarts with `docker compose`
5. Runs a smoke test against `/healthz/` on the server

Step-by-step AWS setup (S3, ECR, IAM role, EC2, Jenkins credentials) is in
[`deploy/AWS_DEPLOY.md`](deploy/AWS_DEPLOY.md).

## Configuration

All settings come from environment variables (or a `.env` file):

| Variable                      | Default                  | Purpose                                 |
|-------------------------------|--------------------------|-----------------------------------------|
| `DJANGO_DEBUG`                | `1` (local), `0` in Docker | Debug mode                             |
| `DJANGO_SECRET_KEY`           | required when debug is off | Django secret key                      |
| `DJANGO_ALLOWED_HOSTS`        | `*` in debug             | Comma-separated hostnames               |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty                    | e.g. `http://<ec2-ip>`                  |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | SQLite | Database connection |
| `AWS_REGION`                  | `ap-south-1`             | AWS region                              |
| `AWS_S3_REPORTS_BUCKET`       | empty (upload disabled)  | Bucket where PDF reports are archived   |

## About the ML model

`ml/build_baseline.py` trains a logistic regression on **synthetic data**: reading
difficulties and low attention raise the risk, and age has a small effect. It shows the
end-to-end pipeline (feature vector → model → stored prediction → report). It is not a
clinically validated screening tool. The next step would be to train on real assessment data
and add the test scores as features.

The model file is a build artifact. The Docker build and CI train it with a fixed seed, so it
is not committed to git.

## Project structure

```
accounts/          custom email-based user model, auth views
assessments/       intake form and the five skill tests
predictions/       model loading + inference service
recommendations/   weakness scoring and resource suggestions
reports/           PDF report, analytics dashboard, S3 upload (storage.py)
ml/                baseline model training script
lddiag/            Django settings, URLs, /healthz/
tests/             test suite
docker/            container entrypoint (runs migrations, then gunicorn)
deploy/            AWS deployment guide
Dockerfile, docker-compose.yml, Jenkinsfile, .github/workflows/ci.yml
```
