#!/bin/bash

set -e

BAZELISK_VERSION=v1.19.0
BAZELISK_SHA384_SUM=cc454c248a90c414bb1774e798ba87ecea6e81127f06c2ba73e93dab51a9159ca67a65deb2cc0b38095314e6a2a7a667

APT_PACKAGES=(
    build-essential
    curl
    git
    unzip
    wget
    zip
    libusb-1.0-0-dev
    # For local Pico tooling
    pkg-config
    cmake
    gcc-arm-none-eabi
    libnewlib-arm-none-eabi
    libstdc++-arm-none-eabi-newlib
    # For local Pico testing
    minicom
)

function install_apt_packages() {
    # Check if apt is available
    if ! check_command apt; then
        echo "apt is not available"
        return 1
    fi

    # Check if apt packages are already installed
    all_installed=true
    missing_packages=()
    for package in ${APT_PACKAGES[@]}; do
        if dpkg -s $package &> /dev/null; then
            continue
        fi
        all_installed=false
        missing_packages+=($package)
    done

    if $all_installed; then
        echo "All apt packages are already installed"
        return 0
    fi

    echo "Installing missing apt packages: ${missing_packages[@]}"

    # Install apt packages
    sudo apt update
    sudo apt install -y ${missing_packages[@]}
}

function filesystem_setup() {
    add_to_path $HOME/.local/bin

    mkdir -p $HOME/.local/share/completions
    # Add ~/.local/share/completions to ~/.bashrc if not already present
    if ! grep -q "source ~/.local/share/completions/*" ~/.bashrc; then
        echo "source ~/.local/share/completions/*" >> ~/.bashrc
    fi
}

function install_bazelisk() {
    # Add bazel-complete.bash to ~/.local/share/completions
    if copy_if_not_up_to_date misc/bazel-complete.bash ~/.local/share/completions false; then
        echo "Copied bazel-complete.bash to ~/.local/share/completions"
    fi

    # Check if bazel is already installed
    if check_command bazel; then
        echo "bazel is already installed"
        return 0
    fi

    # Install bazelisk from release
    wget https://github.com/bazelbuild/bazelisk/releases/download/$BAZELISK_VERSION/bazelisk-linux-amd64 -O ~/.local/bin/bazel

    # Verify bazelisk checksum
    verify_sha384sum ~/.local/bin/bazel $BAZELISK_SHA384_SUM

    # Make bazel executable
    chmod +x ~/.local/bin/bazel

    # Verify bazel is installed
    bazel version
}

function copy_udev_rules() {
    # Copy all files from misc/udev to /etc/udev/rules.d
    all_installed=true
    missing_files=()
    for file in misc/udev/*; do
        if copy_if_not_up_to_date $file /etc/udev/rules.d true; then
            all_installed=false
            missing_files+=($file)
        fi
    done

    if $all_installed; then
        echo "udev rules are already copied"
        return 0
    fi

    echo "Copied udev rules: ${missing_files[@]}"

    sudo service udev restart
    sudo udevadm control --reload-rules
}


#
# Helpers
#

function add_to_path() {
    local path=$1
    mkdir -p $path
    # Add $path to PATH in ~/.bashrc if not already present,
    # then export the new PATH
    if ! grep -q "PATH=\"$path:\$PATH\"" ~/.bashrc; then
        echo "PATH=\"$path:\$PATH\"" >> ~/.bashrc
    fi
    export PATH="$path:$PATH"
}

function verify_sha384sum() {
    local file=$1
    local sha384sum=$2
    local actual_sha384sum=$(sha384sum $file | cut -d' ' -f1)
    if [ "$sha384sum" != "$actual_sha384sum" ]; then
        echo -e "\e[31msha384sum mismatch for $file"
        echo "Expected: $sha384sum"
        echo -e "Actual: $actual_sha384sum\e[0m"
        exit 1
    fi
}

function check_command() {
    local command=$1
    if ! command -v $command &> /dev/null; then
        echo "$command not found"
        return 1
    fi

    return 0
}

function success() {
    echo -e "\e[32m"
    echo "(っ◔◡◔)っ ♥success♥"
    echo -e "\e[0m"
}

function copy_if_not_up_to_date() {
    # Copy $src to $dest if $dest/$(basename $src) does not exist
    # or if the destination file is not up to date
    # Returns 0 if file is copied, 1 otherwise
    local src=$1
    local dest=$2
    local needs_sudo=$3
    if [ ! -f $dest/$(basename $src) ] || [ $(stat -c %Y $src) -gt $(stat -c %Y $dest/$(basename $src)) ]; then
        if $needs_sudo; then
            sudo cp $src $dest
            echo "Copied $src to $dest/$(basename $src)"
            return 0
        else
            cp $src $dest
            return 0
        fi
    fi
    return 1
}

install_apt_packages
filesystem_setup
install_bazelisk
copy_udev_rules
success
