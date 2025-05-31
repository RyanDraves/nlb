#!/bin/bash
#
# Publish the Python package to PyPI or TestPyPI.

set -e
set -o pipefail

# Get the directory of repo root
script_dir=$(dirname "$(realpath "$0")")
repo_root=$(realpath "$script_dir/../../..")

if [[ "$1" != "pypi" && "$1" != "testpypi" ]]; then
    echo "Usage: $0 [pypi|testpypi]"
    exit 1
fi

function publish() {
    local repository="$1"

    # Read the version from nlb/python_VERSION.txt
    version=$(cat "$repo_root/tools/release/python/python_VERSION.txt" | tr -d '[:space:]')

    if [[ -z "$version" ]]; then
        echo "Version not found in tools/release/python/python_VERSION.txt"
        exit 1
    fi

    echo "Publishing version $version to $repository..."
    # Run the publish command with the specified repository
    bazel run \
        --config quiet \
        --config stamp \
        --config "$repository" \
        --embed_label="$version" \
        //nlb:nlb_wheel.publish \
        -- --repository "$repository" || {
            echo "Failed to publish to $repository"
            exit 1
        }

    echo "Successfully published version $version to $repository"
}

function success() {
    echo -e "\e[32m"
    echo "(っ◔◡◔)っ ♥success♥"
    echo -e "\e[0m"
}

publish "$1"
success
