#!/bin/bash
#
# Prepare //nlb/BUILD for a Python release.

set -e
set -o pipefail

# Get the directory of repo root
script_dir=$(dirname "$(realpath "$0")")
repo_root=$(realpath "$script_dir/../../..")

function update_deps() {
    # Query for all Python modules in //nlb/ and add them to //nlb:all_python_modules
    all_python_modules=$(
        bazel query '
            kind(py_binary, //nlb/...) +
            kind(py_library, //nlb/...) -
            attr(tags, testdata, //nlb/...)
        '
    )

    # Create a temp file to write Buildozer commands
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT
    for label in $all_python_modules; do
        echo "add deps $label|//nlb:all_python_modules" >> "$temp_file"
    done

    # Run Buildozer to update the BUILD file, allow non-zero exit code
    buildozer -f "$temp_file" || true
}

function update_completion_data_files() {
    # Query for all completion files and update the data files in //nlb:nlb_wheel
    # Completion rules end with `_completions` and are genrules
    completion_files=$(
        bazel query 'kind(genrule, //nlb/...) intersect attr(name, _completions, //nlb/...)'
    )

    # Query the existing data_files keys in //nlb:all_data_files
    existing_data_files=$(bazel query 'labels(data_files, //nlb:nlb_wheel)')

    # Create a temp file to write Buildozer commands
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT
    for label in $completion_files; do
        # Skip if the completion file is already in data_files
        if echo "$existing_data_files" | grep -q "$label"; then
            continue
        fi

        # Extract the name of the completion file from Bazel label (format: //path:label)
        completion_name=$(echo "$label" | awk -F: '{print $2}' | sed 's/_completions//')
        # Encode the `:` in the label as `%` for Buildozer
        # https://github.com/bazelbuild/buildtools/issues/982
        # (Fixed on main -> needs release + `buildifier_prebuilt` update)
        escaped_label=$(echo "$label" | sed 's/:/%/')
        echo "dict_add data_files $escaped_label:data/share/completions/${completion_name}-completion.bash|//nlb:nlb_wheel" >> "$temp_file"
    done

    # Run Buildozer to update the BUILD file
    buildozer -f "$temp_file"

    # Replace the `%` back to `:` in the BUILD file
    sed -i 's/%/:/g' "$repo_root/nlb/BUILD"

    # Run buildifier to format the BUILD file
    buildifier "$repo_root/nlb/BUILD" || true
}

function update_entry_points() {
    # Query for all Python binaries and update the entry points in //nlb:nlb_wheel
    python_binaries=$(
        bazel query 'kind(py_binary, //nlb/...)'
    )

    # Create a temp file to write Buildozer commands
    temp_file=$(mktemp)
    trap 'rm -f "$temp_file"' EXIT
    for label in $python_binaries; do
        # Extract the name of the binary from the Bazel label (format: //path:label)
        binary_name=$(echo "$label" | awk -F: '{print $2}')
        # Extract the package path from the Bazel label (output: path.label)
        package_path=$(echo "$label" | sed 's|//||' | sed 's/:/./' | sed 's|/|.|g')

        echo "dict_list_add entry_points console_scripts $binary_name\ =\ $package_path:main|//nlb:nlb_wheel" >> "$temp_file"
    done

    # Run Buildozer to update the BUILD file
    buildozer -f "$temp_file" || true
}

function update_version() {
    local bump_type=$1

    if [[ -z "$bump_type" ]]; then
        return
    fi

    # Read the version from nlb/VERSION.txt
    version=$(cat "$repo_root/tools/release/python/VERSION.txt" | tr -d '[:space:]')

    if [[ -z "$version" ]]; then
        echo "Version not found in tools/release/python/VERSION.txt"
        exit 1
    fi

    # Calculate the new version based on the bump type
    if [[ "$bump_type" == 'major' ]]; then
        new_version=$(echo "$version" | awk -F. '{print $1+1".0.0"}')
    elif [[ "$bump_type" == 'minor' ]]; then
        new_version=$(echo "$version" | awk -F. '{print $1"."$2+1".0"}')
    elif [[ "$bump_type" == 'patch' ]]; then
        new_version=$(echo "$version" | awk -F. '{print $1"."$2"."$3+1}')
    else
        echo "Unknown bump type: $bump_type"
        exit 1
    fi

    # Update the version file
    echo "$new_version" > "$repo_root/tools/release/python/VERSION.txt"
    echo "Updated version to $new_version in tools/release/python/VERSION.txt"
}

function success() {
    echo -e "\e[32m"
    echo "(っ◔◡◔)っ ♥success♥"
    echo -e "\e[0m"
}

if [[ "$1" == '--bump-major' ]]; then
    bump_type='major'
elif [[ "$1" == '--bump-minor' ]]; then
    bump_type='minor'
elif [[ "$1" == '--bump-patch' ]]; then
    bump_type='patch'
elif [[ -z "$1" ]]; then
    bump_type=''
else
    echo "Usage: $0 [--bump-major|--bump-minor|--bump-patch]"
    exit 1
fi

update_deps
update_completion_data_files
update_entry_points
update_version $bump_type
success
