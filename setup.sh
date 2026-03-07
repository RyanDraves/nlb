#!/bin/bash
#
# This script sets up the environment with the following:
# - apt packages
# - bazelisk
# - udev rules
# - Ryan's custom settings (optional)
#     - gh
#     - vscode keybindings
#     - gh alias
#
# It probably works on anything Linux x86_64 / ARM64 that's Debian / Ubuntu based, but YMMV.
#
# Usage:
#     ./setup.sh

set -e
set -o pipefail

BAZELISK_VERSION=v1.27.0
BAZELISK_X86_SHA256_SUM=e1508323f347ad1465a887bc5d2bfb91cffc232d11e8e997b623227c6b32fb76
BAZELISK_ARM64_SHA256_SUM=bb608519a440d45d10304eb684a73a2b6bb7699c5b0e5434361661b25f113a5d
BAZELISK_ARM64_MACOS_SHA256_SUM=8bf08c894ccc19ef37f286e58184c3942c58cb08da955e990522703526ddb720

GH_VERSION="2.83.2"
GH_X86_SHA256_SUM=ca6e7641214fbd0e21429cec4b64a7ba626fd946d8f9d6d191467545b092015e
GH_ARM64_SHA256_SUM=b1a0c0a0fcf18524e36996caddc92a062355ed014defc836203fe20fba75a38e
GH_ARM64_MACOS_SHA256_SUM=ba3e0396ebbc8da17256144ddda503e4e79c8b502166335569f8390d6b75fa8d

# Go is exported by multitool, but we need it for the Go extension to be happy
GO_VERSION=$(grep '^go ' go.mod | awk '{print $2}')
GO_X86_SHA256_SUM=aac1b08a0fb0c4e0a7c1555beb7b59180b05dfc5a3d62e40e9de90cd42f88235
GO_ARM64_SHA256_SUM=bd03b743eb6eb4193ea3c3fd3956546bf0e3ca5b7076c8226334afe6b75704cd
GO_MACOS_ARM64_SHA256_SUM=9c8fcb30a922a845ed3733bd4afdd67b5aa8d43c9ecce0d4d11e832437a52126

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
    # System interpreter packages
    python-is-python3
    python3-pip
    python3-ipython
    python3-numpy
    # For local Pico tooling
    pkg-config
    cmake
    # For local Pico testing
    minicom
    # DB
    libpq-dev
    # Copying
    xclip
    # Dev tools
    direnv
    tmux
)

BREW_PACKAGES=(
    curl
    git
    git-lfs
    wget
    openjdk
    tree
    htop
    # System interpreter packages
    python3
    ipython
    numpy
    # For local Pico tooling
    pkg-config
    cmake
    # For local Pico testing
    minicom
    # DB
    libpq
    # Dev tools
    direnv
    tmux
)

function check_if_on_wsl() {
    if uname -r | grep -q "WSL"; then
        return 0
    fi
    return 1
}

function is_macos() {
    [[ "$(uname)" == "Darwin" ]]
}

function is_linux() {
    [[ "$(uname)" == "Linux" ]]
}

function get_shell_rc_file() {
    # Detect the current shell and return the appropriate RC file
    if [[ -n "$ZSH_VERSION" ]] || [[ "$SHELL" == */zsh ]]; then
        shell_file="$HOME/.zshrc"
    else
        shell_file="$HOME/.bashrc"
    fi

    # If the shell rc file does not exist, create it
    if [ ! -f "$shell_file" ]; then
        touch "$shell_file"
    fi

    echo "$shell_file"
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

function install_brew_packages() {
    local packages=("$@")

    # Check if brew is available
    if ! check_command brew; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add brew to PATH for Apple Silicon Macs
        if [[ -f /opt/homebrew/bin/brew ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi

    # Check if brew packages are already installed
    all_installed=true
    missing_packages=()
    for package in "${packages[@]}"; do
        if brew list "$package" &> /dev/null; then
            continue
        fi
        all_installed=false
        missing_packages+=("$package")
    done

    if $all_installed; then
        echo "All brew packages are already installed"
        return 0
    fi

    echo "Installing missing brew packages: ${missing_packages[@]}"

    # Install brew packages
    brew install "${missing_packages[@]}"
}

function install_system_packages() {
    if is_macos; then
        install_brew_packages "${BREW_PACKAGES[@]}"
    elif is_linux; then
        install_apt_packages "${APT_PACKAGES[@]}"
    else
        echo "Unsupported OS: $(uname)"
        return 1
    fi
}

function filesystem_setup() {
    local shell_rc=$(get_shell_rc_file)

    add_to_path $HOME/.local/bin

    mkdir -p $HOME/.local/share/completions
    maybe_add_to_file "$shell_rc" "source $HOME/.local/share/completions/*"

    # Set JAVA_HOME based on OS
    if is_macos; then
        # macOS sets JAVA_HOME differently
        if [[ -x /usr/libexec/java_home ]]; then
            maybe_add_to_file "$shell_rc" 'export JAVA_HOME=$(/usr/libexec/java_home 2>/dev/null || echo "")'
        fi
    else
        maybe_add_to_file "$shell_rc" "export JAVA_HOME=/usr/lib/jvm/default-java"
    fi

    # Setup Git LFS
    git lfs install

    # Setup user bazelrc with BuildBuddy configuration
    setup_user_bazelrc
}

function setup_user_bazelrc() {
    local bazelrc_file="$REPO_ROOT/.user.bazelrc"

    # Check if file exists and has BuildBuddy config
    if [ -f "$bazelrc_file" ] && grep -q "x-buildbuddy-api-key" "$bazelrc_file"; then
        echo ".user.bazelrc already configured"
        return 0
    fi

    # Create file with template if it doesn't exist or is missing BuildBuddy config
    if [ ! -f "$bazelrc_file" ]; then
        cat > "$bazelrc_file" << 'EOF'
common --color=yes
build --disk_cache=~/.cache/bazel
build --remote_header=x-buildbuddy-api-key=[insert secret here]
EOF
        echo -e "${CYAN}${BOLD}"
        echo "----------------------------------------"
        echo "Created .user.bazelrc with BuildBuddy template"
        echo "Please update x-buildbuddy-api-key with your actual API key"
        echo "----------------------------------------"
        echo -e "${RESET}"
    else
        # File exists but doesn't have BuildBuddy config, append it
        cat >> "$bazelrc_file" << 'EOF'
build --disk_cache=~/.cache/bazel
build --remote_header=x-buildbuddy-api-key=[insert secret here]
EOF
        echo -e "${CYAN}${BOLD}"
        echo "----------------------------------------"
        echo "Added BuildBuddy configuration to .user.bazelrc"
        echo "Please update x-buildbuddy-api-key with your actual API key"
        echo "----------------------------------------"
        echo -e "${RESET}"
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

    local os_suffix="linux"
    local arch_suffix="amd64"
    local expected_sum=$BAZELISK_X86_SHA256_SUM

    if is_macos; then
        os_suffix="darwin"
    fi

    if [[ "$(uname -m)" == "aarch64" ]] || [[ "$(uname -m)" == "arm64" ]]; then
        arch_suffix="arm64"
        if is_macos; then
            expected_sum=$BAZELISK_ARM64_MACOS_SHA256_SUM
        else
            expected_sum=$BAZELISK_ARM64_SHA256_SUM
        fi
    fi

    local bazelisk_url="https://github.com/bazelbuild/bazelisk/releases/download/$BAZELISK_VERSION/bazelisk-${os_suffix}-${arch_suffix}"

    # Download appropriate bazelisk binary
    if check_command wget; then
        wget --no-verbose "$bazelisk_url" -O ~/.local/bin/bazel
    else
        curl -fsSL "$bazelisk_url" -o ~/.local/bin/bazel
    fi

    # Verify checksum
    verify_sha256sum ~/.local/bin/bazel $expected_sum

    # Make bazel executable
    chmod +x ~/.local/bin/bazel

    # Verify bazel is installed
    bazel version
}

function install_go() {
    # Check if go is already installed and has the correct version
    if check_command go; then
        installed_version=$(go version | awk '{print $3}' | sed 's/go//')
        if [[ "$installed_version" == "$GO_VERSION" ]]; then
            echo "Go $GO_VERSION is already installed"
            return 0
        else
            echo "Go is installed but version is $installed_version, expected $GO_VERSION"
        fi
    fi

    echo "Installing Go $GO_VERSION"

    local os_suffix="linux-amd64"
    local expected_sum=$GO_X86_SHA256_SUM

    if [[ "$(uname -m)" == "aarch64" ]] || [[ "$(uname -m)" == "arm64" ]]; then
        os_suffix="${os_suffix/amd64/arm64}"
        if is_macos; then
            expected_sum=$GO_MACOS_ARM64_SHA256_SUM
        else
            expected_sum=$GO_ARM64_SHA256_SUM
        fi
    fi

    local go_url="https://golang.org/dl/go${GO_VERSION}.${os_suffix}.tar.gz"
    local go_file="/tmp/go.tar.gz"

    if check_command wget; then
        wget --no-verbose "$go_url" -O "$go_file"
    else
        curl -fsSL "$go_url" -o "$go_file"
    fi

    verify_sha256sum "$go_file" $expected_sum

    # Remove any existing Go installation in ~/.local/go
    if [ -d "$HOME/.local/go" ]; then
        rm -rf "$HOME/.local/go"
    fi

    # Extract Go to ~/.local
    tar -C "$HOME/.local" -xzf "$go_file"

    # Add Go bin directory to PATH
    add_to_path "$HOME/.local/go/bin"

    # Verify Go is installed with the correct version
    version=$(go version)
    if ! echo $version | grep -q "go$GO_VERSION"; then
        echo -e "\e[31mGo is not installed correctly\e[0m"
        echo "Expected version: go$GO_VERSION"
        echo "Actual version: $version"
        exit 1
    fi

    echo "Go $GO_VERSION installed successfully"
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

function arduino_setup() {
    if ! check_command arduino-cli; then
        echo "Installing Arduino CLI"
        curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=$HOME/.local/bin sh
    else
        echo "Arduino CLI already installed"
    fi

    # Check if arduino-avr core is already installed
    if arduino-cli core list | grep -q "arduino:avr"; then
        echo "arduino:avr core already installed"
        return 0
    fi

    echo "Installing arduino:avr core"
    arduino-cli core update-index
    arduino-cli core install arduino:avr
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

function dev_env_setup() {
    local shell_rc=$(get_shell_rc_file)

    echo "Exporting venv..."
    bazel run //:venv
    # Allow local files to be used
    venv/bin/pip install -e .
    echo "Done exporting venv"

    # Setup direnv with the appropriate shell hook
    if [[ "$shell_rc" == *"zshrc"* ]]; then
        maybe_add_to_file "$shell_rc" 'eval "$(direnv hook zsh)"'
    else
        maybe_add_to_file "$shell_rc" 'eval "$(direnv hook bash)"'
    fi

    echo "Allowing direnv in repo root"
    cd $REPO_ROOT
    direnv allow
    cd - > /dev/null

    # Build dev environment
    bazel run //tools:bazel_env
}

#
# Ryan's custom settings
#

function setup_ryans_custom_settings() {
    setup_gh
    if is_linux; then
        install_apt_packages "${RYANS_APT_PACKAGES[@]}"
    fi
    install_vscode_keybindings misc/dravesr/keybindings.json
    setup_bash_aliases
    # Not working on MacOS yet
    if is_linux; then
        install_system_python_packages
    fi
}

function setup_gh() {
    install_gh
    authenticate_gh
    make_gh_alias feature '!nlb_gh_feature $@' -s
    make_gh_alias merge 'pr merge -s -d'
    install_gh_extension github/gh-copilot
}

function install_gh() {
    # Check if gh is already installed and has the correct version
    if [[ "$(gh --version)" == *"$GH_VERSION"* ]]; then
        echo "gh is already installed"
        return 0
    fi

    echo "Installing gh v$GH_VERSION"

    local os_suffix="linux"
    local arch_suffix="amd64"
    local expected_sum=$GH_X86_SHA256_SUM
    local file_ext="tar.gz"

    if is_macos; then
        os_suffix="macOS"
        file_ext="zip"
    fi

    if [[ "$(uname -m)" == "aarch64" ]] || [[ "$(uname -m)" == "arm64" ]]; then
        arch_suffix="arm64"
        if is_macos; then
            expected_sum=$GH_ARM64_MACOS_SHA256_SUM
        else
            expected_sum=$GH_ARM64_SHA256_SUM
        fi
    fi

    local gh_url="https://github.com/cli/cli/releases/download/v$GH_VERSION/gh_${GH_VERSION}_${os_suffix}_${arch_suffix}.${file_ext}"
    local gh_file="/tmp/gh.${file_ext}"

    if check_command wget; then
        wget --no-verbose $gh_url -O "$gh_file"
    else
        curl -fsSL $gh_url -o "$gh_file"
    fi

    verify_sha256sum "$gh_file" $expected_sum

    # Unpack based on file type
    if is_macos; then
        # macOS uses zip
        unzip -q "$gh_file" -d /tmp/gh_extract
        cp -R /tmp/gh_extract/gh_${GH_VERSION}_${os_suffix}_${arch_suffix}/* ~/.local/
        rm -rf /tmp/gh_extract
    else
        # Linux uses tar.gz
        tar -xzf "$gh_file" -C ~/.local --strip-components=1
    fi

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
    shift 2
    local additional_args=("$@")

    # Check if alias exists
    if gh alias list | grep -q "^$alias:"; then
        # Escape special regex characters in the command for matching
        local escaped_command=$(printf '%s\n' "$command" | sed 's/[[\.*^$/]/\\&/g')
        # Check if the command matches (gh may wrap commands in quotes or not)
        if gh alias list | grep -qE "^$alias: ('$escaped_command'|$escaped_command)$"; then
            echo "gh alias $alias already exists"
            return 0
        fi
        echo "Updating gh alias $alias"
        gh alias set --clobber $alias "$command" "${additional_args[@]}"
    else
        echo "Creating gh alias $alias"
        gh alias set $alias "$command" "${additional_args[@]}"
    fi
}

function install_gh_extension() {
    local extension=$1
    # Check if gh extension is already installed
    if gh extension list | grep -q "$extension"; then
        echo "gh extension $extension already installed"
        return 0
    fi

    echo "Installing gh extension $extension"
    gh extension install $extension
}

function install_vscode_keybindings() {
    local repo_keybindings_file=$1

    if check_if_on_wsl; then
        windows_user=$(powershell.exe '$env:UserName' | tr -d '\r')
        keybindings_file=/mnt/c/Users/$windows_user/AppData/Roaming/Code/User/keybindings.json
    elif is_macos; then
        keybindings_file="$HOME/Library/Application Support/Code/User/keybindings.json"
    else
        keybindings_file=$HOME/.config/Code/User/keybindings.json
    fi

    if copy_if_not_up_to_date $repo_keybindings_file "$keybindings_file" false; then
        echo "Copied $repo_keybindings_file to $keybindings_file"
    fi
}

function setup_bash_aliases() {
    echo "Setting up shell aliases"
    local shell_rc=$(get_shell_rc_file)
    local aliases_file="$HOME/.bash_aliases"

    # For zsh, we can use the same file and source it from zshrc
    if [[ "$shell_rc" == *"zshrc"* ]]; then
        maybe_add_to_file "$shell_rc" "[[ -f ~/.bash_aliases ]] && source ~/.bash_aliases"
    fi

    local bash_aliases_lines=(
        "# Turn on tap-to-click"
        "alias silent_mode='gsettings set org.gnome.desktop.peripherals.touchpad tap-to-click true'"
        "# Remember why we turned off tap-to-click"
        "alias fuck_silent_mode='gsettings set org.gnome.desktop.peripherals.touchpad tap-to-click false'"
        "# Matlab usability"
        "alias matlab='matlab -nodesktop -nosplash'"
        "# Output SHA256 integrity hashes as Bazel wants them"
        "function bazel_sha256() {
    openssl dgst -sha256 -binary \"\$1\" | openssl base64 -A | sed 's/^/sha256-/'
    echo ""  # Newline
        }"
        "# List recent branches"
        "function recent_branches() {
    git branch --sort=-committerdate | head -n \"\${1:-8}\"
}"
    )

    maybe_add_to_file "$aliases_file" "${bash_aliases_lines[@]}"
}

function install_system_python_packages() {
    if is_macos; then
        # On macOS, use Homebrew's pip3
        /opt/homebrew/bin/pip3 install nl-blocks --upgrade --break-system-packages
    else
        # Big scary flag, but that won't stop the fun
        /usr/bin/pip install nl-blocks --upgrade --break-system-packages
    fi
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

run_section() {
    SECTION_MESSAGE="$1"
    shift  # Remove the first argument

    echo -e "\n${BOLD}${CYAN}➤ $SECTION_MESSAGE...${RESET}\n"

    if "$@"; then
        echo -e "${GREEN}${BOLD}[✔] ${RESET}$SECTION_MESSAGE\n"
    else
        echo -e "${RED}${BOLD}[✘] ${RESET}$SECTION_MESSAGE (Failed!)\n"
        exit 1
    fi
}

function add_to_path() {
    local path=$1
    local shell_rc=$(get_shell_rc_file)
    mkdir -p $path
    maybe_add_to_file "$shell_rc" "PATH=\"$path:\$PATH\""
    # Export to make the new PATH available in the current shell
    export PATH="$path:$PATH"
}

function verify_sha256sum() {
    local file=$1
    local sha256sum=$2
    local actual_sha256sum=$(sha256sum $file | cut -d' ' -f1)
    if [ "$sha256sum" != "$actual_sha256sum" ]; then
        echo -e "\e[31msha256sum mismatch for $file"
        echo "Expected: $sha256sum"
        echo -e "Actual: $actual_sha256sum\e[0m"
        exit 1
    fi
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

function maybe_add_to_file() {
    local file=$1
    shift
    local lines=("$@")
    for line in "${lines[@]}"; do
        echo $line
        echo $file
        if ! grep -qF "$line" "$file"; then
            echo "$line" >> "$file"
        fi
    done
}

function success() {
    printf "\e[32m\n"
    echo "(っ◔◡◔)っ ♥success♥"
    printf "\e[0m\n"
}

function get_file_mtime() {
    # Get modification time of a file (cross-platform)
    local file=$1
    if is_macos; then
        stat -f %m "$file"
    else
        stat -c %Y "$file"
    fi
}

function copy_if_not_up_to_date() {
    # Copy $src to $dest if destination does not exist or is not up to date
    # If $dest is a directory, the file will be copied into it
    # If $dest is a file path, it will be copied to that exact location
    # Returns 0 if file is copied, 1 otherwise
    local src=$1
    local dest=$2
    local needs_sudo=$3

    # Determine the destination file path
    local dest_file
    if [ -d "$dest" ]; then
        # dest is a directory, append basename
        dest_file="$dest/$(basename "$src")"
    else
        # dest is a file path (directory might not exist yet)
        dest_file="$dest"
        # Create parent directory if it doesn't exist
        local dest_dir=$(dirname "$dest")
        if [ ! -d "$dest_dir" ]; then
            if $needs_sudo; then
                sudo mkdir -p "$dest_dir"
            else
                mkdir -p "$dest_dir"
            fi
        fi
    fi

    # Check if copy is needed
    if [ ! -f "$dest_file" ] || [ $(get_file_mtime "$src") -gt $(get_file_mtime "$dest_file") ]; then
        if $needs_sudo; then
            sudo cp "$src" "$dest_file"
            echo "Copied $src to $dest_file"
            return 0
        else
            cp "$src" "$dest_file"
            return 0
        fi
    fi
    return 1
}

run_section "Install system packages" install_system_packages
run_section "Filesystem setup" filesystem_setup
run_section "Install Bazelisk" install_bazelisk
run_section "Install Go" install_go
if is_linux; then
    run_section "Copy udev rules" copy_udev_rules
    run_section "Setup Arduino CLI" arduino_setup
fi
if is_linux; then
    run_section "Install docker" install_docker
fi
run_section "Setup dev environment" dev_env_setup
# Check if user is `dravesr` before setting up Ryan's environment
if [ "$USER" = "dravesr" ]; then
    run_section "Apply Ryan's dev settings" setup_ryans_custom_settings
fi
success
