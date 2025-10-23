#!/usr/bin/env bash

COMMIT_SHA=$(git rev-parse HEAD)
REPO=$(git config --get remote.origin.url)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "STABLE_REPO ${REPO}"
echo "STABLE_BRANCH ${BRANCH}"
echo "COMMIT_SHA ${COMMIT_SHA}"
