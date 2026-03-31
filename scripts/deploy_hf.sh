#!/usr/bin/env bash
# deploy_hf.sh — Push VerifAI to Hugging Face Spaces
# Usage: bash scripts/deploy_hf.sh
#
# Prerequisites:
#   - git-lfs installed: https://git-lfs.github.com
#   - HF Space already created at https://huggingface.co/spaces/<username>/verifai
#   - HF_USERNAME and HF_SPACE_NAME env vars set, OR edit the HF_SPACE_URL below.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

HF_USERNAME="${HF_USERNAME:-your-hf-username}"
HF_SPACE_NAME="${HF_SPACE_NAME:-verifai}"
HF_SPACE_URL="https://huggingface.co/spaces/${HF_USERNAME}/${HF_SPACE_NAME}"

echo "=== VerifAI — Hugging Face Spaces Deployment ==="
echo "Target: $HF_SPACE_URL"
echo ""

# Add HF Space as a remote (if not already)
if ! git remote | grep -q "hf-space"; then
  echo "Adding HF Space remote..."
  git remote add hf-space "https://huggingface.co/spaces/${HF_USERNAME}/${HF_SPACE_NAME}.git"
fi

echo "Pushing to Hugging Face Spaces..."
git push hf-space main

echo ""
echo "Deployment complete! View your Space at:"
echo "  $HF_SPACE_URL"
