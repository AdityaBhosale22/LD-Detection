# Deploying to AWS (EC2 + ECR + S3)

This is the Jenkins CD path for the API. The public demo runs on Vercel + Render instead
(see [LIVE_DEPLOY.md](LIVE_DEPLOY.md)), because a browser app served over HTTPS needs an HTTPS API.
To point the Vercel frontend at EC2, put the instance behind HTTPS first (for example Caddy plus a domain).

This setup fits in the AWS free tier: one `t2.micro`/`t3.micro` EC2 instance, one ECR
repository, and one S3 bucket. Region used below: `ap-south-1`. Change it if you need to.

```
GitHub ──push──▶ GitHub Actions (CI: tests + docker build)
   │
   └──▶ Jenkins (CD) ──build/test──▶ push image ──▶ ECR
                                                   │
                         ssh: docker compose pull ◀┘
                                   │
                              EC2 instance
                    ┌──────────────┴──────────────┐
                    web (gunicorn :80)    db (PostgreSQL)
                    │
                    └── PDF reports ──▶ S3 bucket (via IAM instance role)
```

## 1. Create the S3 bucket and ECR repository

```bash
aws s3api create-bucket --bucket <your-reports-bucket> --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1
aws s3api put-public-access-block --bucket <your-reports-bucket> \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws ecr create-repository --repository-name ld-detection --region ap-south-1
```

## 2. Create an IAM role for the EC2 instance

In IAM, create a role for the **EC2** service and attach:

- `AmazonEC2ContainerRegistryReadOnly` (managed policy) so the instance can pull the image
- this inline policy so the app can write reports to the bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject"],
    "Resource": "arn:aws:s3:::<your-reports-bucket>/reports/*"
  }]
}
```

The app uses boto3's default credential chain, so it picks up this role
automatically. No access keys are stored on the server.

## 3. Launch the EC2 instance

- AMI: Amazon Linux 2023, type `t2.micro` or `t3.micro`
- IAM instance profile: the role from step 2
- Security group: SSH (22) from your IP only, HTTP (80) from anywhere
- Key pair: download it and add it to Jenkins as the `ec2-ssh-key` credential

SSH in and install Docker and the Compose plugin:

```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# 1 GB swap helps on a 1 GB instance
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024 && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

Log out and back in so the `docker` group applies. Then create the app folder and its `.env`:

```bash
mkdir -p ~/app && cd ~/app
cat > .env <<'EOF'
DJANGO_SECRET_KEY=<long random string>
DJANGO_ALLOWED_HOSTS=<ec2-public-ip-or-dns>
DJANGO_CSRF_TRUSTED_ORIGINS=http://<ec2-public-ip-or-dns>
DB_PASSWORD=<strong password>
CORS_ALLOWED_ORIGINS=<your frontend URL, e.g. https://ld-detection.vercel.app>
AWS_REGION=ap-south-1
AWS_S3_REPORTS_BUCKET=<your-reports-bucket>
WEB_PORT=80
EOF
```

## 4. Configure Jenkins

1. Install the plugins **Pipeline**, **Docker Pipeline**, **SSH Agent** and **Credentials Binding**. The Jenkins agent also needs `docker` and the AWS CLI v2.
2. Add the credentials:
   - `aws-ecr-push`: *Username with password*, holding an IAM user's access key ID and secret. That user needs `AmazonEC2ContainerRegistryPowerUser`.
   - `ec2-ssh-key`: *SSH Username with private key*, with username `ec2-user` and the key pair from step 3.
3. Edit `AWS_ACCOUNT_ID` and `EC2_HOST` at the top of the `Jenkinsfile`.
4. Create a **Multibranch Pipeline** (or Pipeline from SCM) job pointing at this repo.

A build on `main` builds the image, runs the tests inside it, pushes `:<build-number>` and
`:latest` to ECR, then SSHes to EC2 to pull the image and restart with `docker compose`.
It finishes with a smoke test against `/healthz/`.

## 5. Verify

```bash
curl http://<ec2-public-ip>/healthz/          # {"status": "ok"}
```

Register and download a report through the API (or a frontend pointed at it). The PDF then
shows up in S3:

```bash
aws s3 ls s3://<your-reports-bucket>/reports/ --recursive
```

## Cost notes

- Stop the EC2 instance when you're not demoing it. The free tier covers 750 hours a month for 12 months.
- ECR's free tier covers 500 MB a month. Old images can be removed with an ECR lifecycle policy.
