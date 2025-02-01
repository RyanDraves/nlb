#!/bin/bash
#
# This script sets up the environment with the following:
# - apt packages
# - bazelisk
# - udev rules
# - Ryan's custom settings (optional)
#     - gh
#     - vscode extensions
#     - vscode keybindings
#     - gh alias
#
# It probably works on anything Linux x86_64 / ARM64 that's Debian / Ubuntu based, but YMMV.
#
# Usage:
#     ./setup.sh

set -e
set -o pipefail

BAZELISK_VERSION=v1.25.0
BAZELISK_X86_SHA384_SUM=f452948139ca10fb2f85b9e9381f103c63978773884a3ee3092685b47556241058c7bc4e5806e5bd1c754076814fd60a
BAZELISK_ARM64_SHA384_SUM=6457888166ac4c3fb5ee82323987bec29e97736caeeee46be2467b54ba27d7095f84271666f992af58978415bbb300a1

GH_VERSION="2.65.0"
GH_X86_SHA384_SUM=12c22b9132a09ac373465586a7eaaf26016ab5c47af3608400ef6d7b513b511b49057e37e8871fadd56a8236502de705
GH_ARM64_SHA384_SUM=aae7887a1c577fcf1696754421e9f3f09e5b9807ef637d0ea29cd515924b255ed0481b0bae1877435ed4e718351ab0df

REPO_ROOT=$(dirname $(readlink -f $0))

APT_PACKAGES=(
    build-essential
    curl
    git
    git-lfs
    unzip
    wget
    default-jdk
    zip
    zlib1g-dev
    libusb-1.0-0-dev
    tree
    htop
    python-is-python3
    python3-pip
    python3-ipython
    python3-numpy
    # For local Pico tooling
    pkg-config
    cmake
    # For local Pico testing
    minicom
)

function check_if_on_wsl() {
    if uname -r | grep -q "WSL"; then
        return 0
    fi
    return 1
}

RYANS_APT_PACKAGES=()
if ! check_if_on_wsl; then
    RYANS_APT_PACKAGES+=(
        code
    )
fi

function install_apt_packages() {
    local packages=("$@")

    # Check if apt is available
    if ! check_command apt; then
        echo "apt is not available"
        return 1
    fi

    # Check if apt packages are already installed
    all_installed=true
    missing_packages=()
    for package in "${packages[@]}"; do
        if dpkg -s "$package" &> /dev/null; then
            continue
        fi
        all_installed=false
        missing_packages+=("$package")
    done

    if $all_installed; then
        echo "All apt packages are already installed"
        return 0
    fi

    echo "Installing missing apt packages: ${missing_packages[@]}"

    # Install apt packages
    sudo apt update
    sudo apt install -y "${missing_packages[@]}"
}

function filesystem_setup() {
    add_to_path $HOME/.local/bin

    mkdir -p $HOME/.local/share/completions
    maybe_add_to_bashrc "source $HOME/.local/share/completions/*"

    maybe_add_to_bashrc "export JAVA_HOME=/usr/lib/jvm/default-java"

    add_to_path $REPO_ROOT/tools/bin

    # Setup Git LFS
    git lfs install
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

    if [[ "$(uname -m)" == "aarch64" ]]; then
        # Install bazelisk for ARM64
        wget https://github.com/bazelbuild/bazelisk/releases/download/$BAZELISK_VERSION/bazelisk-linux-arm64 -O ~/.local/bin/bazel
        verify_sha384sum ~/.local/bin/bazel $BAZELISK_ARM64_SHA384_SUM
    else
        # Install bazelisk from release
        wget https://github.com/bazelbuild/bazelisk/releases/download/$BAZELISK_VERSION/bazelisk-linux-amd64 -O ~/.local/bin/bazel

        # Verify bazelisk checksum
        verify_sha384sum ~/.local/bin/bazel $BAZELISK_X86_SHA384_SUM
    fi

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

function install_docker() {
    # Check if docker is already installed
    if check_command docker; then
        echo "docker is already installed"
        return 0
    fi

    os_id=$(. /etc/os-release && echo "$ID")

    # Add Docker's official GPG key:
    sudo apt update
    sudo apt install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/${os_id}/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${os_id} \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update

    # Install packages
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add user to docker group
    sudo usermod -aG docker $USER

    # Notify user to log out and back in
    echo -e "\e[36m"
    echo "----------------------------------------"
    echo "Please log out and back in to use docker without sudo"
    echo "----------------------------------------"
    echo -e "\e[0m"
}


function setup_venv() {
    echo "Exporting venv..."
    time bazel run //:venv venv
    echo "Done exporting venv"
}

#
# Ryan's custom settings
#

function setup_ryans_custom_settings() {
    setup_gh
    install_apt_packages "${RYANS_APT_PACKAGES[@]}"
    install_vscode_keybindings misc/dravesr/keybindings.json
    setup_user_bazelrc
}

function setup_gh() {
    install_gh
    authenticate_gh
    make_gh_alias feature 'issue develop "$1" -c'
    make_gh_alias merge 'pr merge -s -d'
}

function install_gh() {
    # Check if gh is already installed and has the correct version
    if [[ "$(gh --version)" == *"$GH_VERSION"* ]]; then
        echo "gh is already installed"
        return 0
    fi

    if [[ "$(uname -m)" == "aarch64" ]]; then
        # Install gh for ARM64
        echo "Installing gh v$GH_VERSION"
        local gh_url="https://github.com/cli/cli/releases/download/v$GH_VERSION/gh_${GH_VERSION}_linux_arm64.tar.gz"

        wget $gh_url -O /tmp/gh.tar.gz
        verify_sha384sum /tmp/gh.tar.gz $GH_ARM64_SHA384_SUM
    else
        # Install gh from release
        echo "Installing gh v$GH_VERSION"
        local gh_url="https://github.com/cli/cli/releases/download/v$GH_VERSION/gh_${GH_VERSION}_linux_amd64.tar.gz"

        wget $gh_url -O /tmp/gh.tar.gz
        verify_sha384sum /tmp/gh.tar.gz $GH_X86_SHA384_SUM
    fi

    # Unpack gh.tar.gz to ~/.local
    tar -xzf /tmp/gh.tar.gz -C ~/.local --strip-components=1

    # Verify is installed with the correct version
    version=$(gh --version)
    if ! echo $version | grep -q $GH_VERSION; then
        echo -e "\e[31mgh is not installed correctly"
        echo "mExpected version: $GH_VERSION"
        echo -e "Actual version: $version\e[0m"
        exit 1
    fi
}

function authenticate_gh() {
    # Check if gh is already authenticated
    if gh auth status | grep -q "Logged in to github.com"; then
        echo "gh is already authenticated"
        return 0
    fi

    # Authenticate gh if the caller is in an interactive shell
    if [[ "$-" == *i* ]]; then
        echo "Authenticating gh"
        gh auth login -p ssh -w
    else
        echo "gh is not authenticated and the caller is not in an interactive shell"
        return 1
    fi
}

function make_gh_alias() {
    local alias=$1
    local command=$2
    # Check if a matching alias and command already exist
    if gh alias list | grep -q "$alias"; then
        if gh alias list | grep -qx "$alias: $command"; then
            echo "gh alias $alias already exists"
            return 0
        fi
        echo "gh alias $alias already exists with a different command"
        gh alias set --clobber $alias "$command"
    else
        echo "Creating gh alias $alias"
        gh alias set $alias "$command"
    fi
}

function install_vscode_keybindings() {
    local repo_keybindings_file=$1

    if check_if_on_wsl; then
        windows_user=$(powershell.exe '$env:UserName' | tr -d '\r')
        keybindings_file=/mnt/c/Users/$windows_user/AppData/Roaming/Code/User/keybindings.json
    else
        keybindings_file=$HOME/.config/Code/User/keybindings.json
    fi

    if copy_if_not_up_to_date $repo_keybindings_file $keybindings_file false; then
        echo "Copied $repo_keybindings_file to $keybindings_file"
    fi
}

function setup_user_bazelrc() {
    echo "Setting up .user.bazelrc"

    cat << EOF > $REPO_ROOT/.user.bazelrc
common --color=yes
EOF
}

#
# Helpers
#

# Colors
GREEN=$(tput setaf 2)
RED=$(tput setaf 1)
CYAN=$(tput setaf 6)
BOLD=$(tput bold)
RESET=$(tput sgr0)

# Trap to restore cursor on exit
cleanup() {
    tput cnorm  # Restore cursor visibility
}
trap cleanup EXIT

# Spinner function - always stays at the last line
spinner() {
    local pid=$1
    local delay=0.1
    local spin_chars=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')

    tput civis  # Hide cursor
    while kill -0 "$pid" 2>/dev/null; do
        for i in "${spin_chars[@]}"; do
            tput sc   # Save cursor position
            tput cup "$(tput lines)" 0  # Move cursor to the last line
            echo -ne "${CYAN}${BOLD}[$i] ${RESET}$SPINNER_MESSAGE   "
            tput rc   # Restore cursor position
            sleep $delay
        done
    done
    tput cnorm  # Restore cursor when done
}

# Function to run a section with a spinner and live logs
run_section() {
    SPINNER_MESSAGE="$1"
    shift  # Remove the first argument

    echo -e "\n${BOLD}${CYAN}➤ $SPINNER_MESSAGE...${RESET}\n"

    # Create a temporary log file
    local log_file
    log_file=$(mktemp)

    # Run the command **in the background**, logging output
    "$@" > "$log_file" 2>&1 &
    local pid=$!

    # Start the spinner (this stays until the command finishes)
    spinner $pid &
    local spinner_pid=$!

    # Live log streaming while the command runs
    tail -f "$log_file" | sed --unbuffered 's/^/  /' &
    local tail_pid=$!

    # Wait for command to finish
    wait $pid
    local exit_code=$?

    # Stop the spinner and log streaming
    kill $spinner_pid 2>/dev/null
    kill $tail_pid 2>/dev/null
    wait $spinner_pid 2>/dev/null || true  # Suppress error message
    wait $tail_pid 2>/dev/null || true

    # Clear spinner line before showing final status
    tput cup "$(tput lines)" 0
    echo -ne "\r\033[K"

    # Show success or failure message
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}${BOLD}[✔] ${RESET}$SPINNER_MESSAGE\n"
    else
        echo -e "${RED}${BOLD}[✘] ${RESET}$SPINNER_MESSAGE (Failed!)\n"
        echo -e "${RED}${BOLD}Error log:${RESET}"
        tail -n 20 "$log_file"  # Show last 20 lines of error log
        exit 1  # Stop execution
    fi
}

function add_to_path() {
    local path=$1
    mkdir -p $path
    maybe_add_to_bashrc "PATH=\"$path:\$PATH\""
    # Export to make the new PATH available in the current shell
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

function maybe_add_to_bashrc() {
    local line=$1
    if ! grep -q "$line" ~/.bashrc; then
        echo "$line" >> ~/.bashrc
    fi
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

run_section "Install apt packages" install_apt_packages "${APT_PACKAGES[@]}"
run_section "Filesystem setup" filesystem_setup
run_section "Install Bazelisk" install_bazelisk
run_section "Copy udev rules" copy_udev_rules
run_section "Install docker" install_docker
run_section "Setup venv" setup_venv
# Check if user is `dravesr` before setting up Ryan's environment
if [ "$USER" = "dravesr" ]; then
    run_section "Apply Ryan's dev settings" setup_ryans_custom_settings
fi
success
