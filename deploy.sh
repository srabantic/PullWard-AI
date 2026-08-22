#!/usr/bin/env bash
# ==============================================================================
# PullWard AI - Google Cloud Run Deployment Script
# ==============================================================================

set -e

SERVICE_NAME="pullward-ai-gateway"
REGION="${GCP_REGION:-us-central1}"
PROJECT_ID="${GCP_PROJECT_ID:-pullward-ai}"

echo "========================================================"
echo "🚀 Deploying PullWard AI to Google Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "========================================================"

# Submit container build to GCP Cloud Build & Deploy to Cloud Run
gcloud config set project "${PROJECT_ID}"

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID}"

echo "========================================================"
echo "✅ PullWard AI successfully deployed to Cloud Run!"
echo "========================================================"
