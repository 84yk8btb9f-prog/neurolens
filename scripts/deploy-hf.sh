#!/usr/bin/env bash
# Deploy the latest backend to the Hugging Face Space.
#
# Prereqs:
#   - You've previously cloned the Space into /tmp/np-space
#   - Your HF write token is configured (git credential helper, or it'll prompt)
#
# Usage:
#   bash scripts/deploy-hf.sh
#
# What it does:
#   1. Pulls latest from the HF Space remote
#   2. Wipes the deployed app dir
#   3. Copies fresh backend files from this repo (Dockerfile, requirements,
#      app/, README front-matter, .gitignore for build hygiene)
#   4. Commits with a timestamped message and pushes
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPACE_DIR="${HF_SPACE_DIR:-/tmp/np-space}"

if [ ! -d "$SPACE_DIR/.git" ]; then
    echo "ERROR: $SPACE_DIR is not a git repo."
    echo "Clone your Space first:"
    echo "  git clone https://huggingface.co/spaces/<your-user>/<your-space> $SPACE_DIR"
    exit 1
fi

echo "→ Syncing $SPACE_DIR with remote..."
cd "$SPACE_DIR"
git pull --rebase --autostash || true

echo "→ Replacing backend files..."
rm -rf app
cp -r "$REPO_ROOT/backend/app" .
cp "$REPO_ROOT/backend/Dockerfile" .
cp "$REPO_ROOT/backend/.dockerignore" .
cp "$REPO_ROOT/backend/requirements.txt" .
cp "$REPO_ROOT/backend/HF_SPACE_README.md" README.md
cp "$REPO_ROOT/backend/.hfspace_gitignore" .gitignore

echo "→ Staging changes..."
git add -A
if git diff --cached --quiet; then
    echo "Nothing to commit. Already up to date."
    exit 0
fi

MSG="${1:-Sync from main repo $(date +%Y-%m-%d-%H%M)}"
git commit -m "$MSG"

echo "→ Pushing to HF Space..."
git push

echo "Done. Watch the build at: https://huggingface.co/spaces/$(git config --get remote.origin.url | sed -E 's|.*spaces/||;s|\.git$||')/tree/main"
