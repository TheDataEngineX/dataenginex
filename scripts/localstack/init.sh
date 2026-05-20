#!/usr/bin/env bash
# LocalStack initialization — runs inside the container on startup.
# Creates the S3 buckets used by dex integration tests.
set -euo pipefail

awslocal s3 mb s3://dex-test-bucket    || true
awslocal s3 mb s3://dex-lakehouse      || true
