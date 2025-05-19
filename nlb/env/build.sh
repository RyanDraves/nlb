#!/bin/bash

# Get the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get the tag as the first argument
tag=$1
if [ -z "$tag" ]; then
  echo "Usage: $0 <tag> [--push]"
  exit 1
fi

docker build -t ghcr.io/ryandraves/env:$tag ${DIR}

# If `--push` is passed, push the image to the registry
if [[ "$*" == *"--push"* ]]; then
  docker push ghcr.io/ryandraves/env:$tag
fi
