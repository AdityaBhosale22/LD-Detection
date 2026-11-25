"""Archive generated PDF reports to Amazon S3.

Enabled only when AWS_S3_REPORTS_BUCKET is set. Credentials come from the normal
boto3 chain: an IAM instance role on EC2, or AWS_* env vars locally.
An S3 failure never blocks the user's download; it is logged instead.
"""
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def upload_report(pdf_bytes: bytes, user_id: int) -> str | None:
	"""Upload a report and return its S3 key, or None if disabled/failed."""
	bucket = settings.AWS_S3_REPORTS_BUCKET
	if not bucket:
		return None

	key = f"reports/user-{user_id}/{timezone.now():%Y%m%d-%H%M%S}.pdf"
	try:
		s3 = boto3.client("s3", region_name=settings.AWS_REGION)
		s3.put_object(Bucket=bucket, Key=key, Body=pdf_bytes, ContentType="application/pdf")
	except (BotoCoreError, ClientError):
		logger.exception("Failed to upload report to s3://%s/%s", bucket, key)
		return None

	logger.info("Uploaded report to s3://%s/%s", bucket, key)
	return key
