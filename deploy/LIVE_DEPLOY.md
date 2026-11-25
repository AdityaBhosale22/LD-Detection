# Live demo: Vercel (frontend) + Render (API) + Neon (database)

All three have free tiers that need no credit card. Expect about 20 minutes.

```
Browser ──▶ Vercel: React app (frontend/)
               │  HTTPS + "Authorization: Token …"
               ▼
           Render: Django API (Dockerfile) ──▶ Neon PostgreSQL
               │
               └──▶ S3 (optional: PDF report archive)
```

## 1. Database: Neon

1. Sign up at <https://neon.tech> and create a project (region: Singapore or Mumbai).
2. Copy the **connection string**. It looks like
   `postgresql://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`

## 2. API: Render

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, then pick this repo. Render reads `render.yaml`.
3. When asked for the `sync: false` variables, enter:
   - `DATABASE_URL`: the Neon connection string
   - `CORS_ALLOWED_ORIGINS`: leave it as `https://example.com` for now, and fix it in step 4
   - The AWS variables are optional. Leave them empty to skip the S3 upload.
4. Wait for the deploy (the first Docker build takes ~5 minutes). Then open
   `https://<your-service>.onrender.com/healthz/`, which should return `{"status": "ok"}`.

Migrations run automatically when the container starts (`docker/entrypoint.sh`).

> The free instance sleeps after 15 minutes without traffic. The first request after that
> takes 30–60 seconds. The frontend pings `/healthz/` when the landing page opens and shows a
> "waking up" message during sign-in.

## 3. Frontend: Vercel

1. In Vercel: **Add New → Project**, then import the repo.
2. Set **Root Directory** to `frontend`. Vercel detects Vite automatically.
3. Add the environment variable `VITE_API_URL` = `https://<your-service>.onrender.com` (no trailing slash).
4. Deploy. `vercel.json` rewrites every path to `index.html`, so deep links like `/dashboard` work.

## 4. Connect them

Back in Render, set `CORS_ALLOWED_ORIGINS` to your Vercel URL, for example
`https://ld-detection.vercel.app` (comma-separate several). Save, and Render redeploys.

Open the Vercel URL, register, and go through the flow: profile, tests, dashboard, then the PDF report.

## Optional: archive reports to S3 from Render

Render has no IAM instance role, so it needs keys. Create an IAM user whose only permission is:

```json
{
  "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow", "Action": "s3:PutObject", "Resource": "arn:aws:s3:::<bucket>/reports/*" }]
}
```

Set `AWS_S3_REPORTS_BUCKET`, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in Render.

## Updating

Pushing to `main` redeploys both automatically. Vercel builds `frontend/`, and Render rebuilds
the Docker image (`autoDeploy: true`).
