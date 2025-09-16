# NLB Monorepo Copilot Instructions

## Project Overview
This is a personal monorepo combining Python libraries, embedded systems, web apps, and self-hosted services. Built with Bazel for polyglot builds and reproducible environments.

## Code Style & Standards
- **Python**: Google Python style guide, single quotes, type hints using Python 3.12+ syntax
- **Formatting**: Ruff with line length 88, single-line imports (except `collections`, `typing`)
- **Bazel**: Starlark files follow Bazel conventions, custom macros in `bzl/`

## Architecture & Key Components

### Core Structure
- `nlb/` - Python library packages (sharetrace, authentik, hyd, etc.)
- `apps/` - Next.js web applications (hyd, iir)
- `emb/` - Embedded C/C++ projects for Raspberry Pi Pico
- `services/` - Docker Compose self-hosted services with Tailscale sidecars
- `bzl/` - Bazel build system extensions and custom rules

### Critical Workflows

**Environment Setup:**
```bash
./setup.sh  # Full system setup with apt packages, Bazelisk, udev rules
bazel run //:requirements.update  # Update Python dependencies
bazel run //:venv venv  # Create venv
source venv/bin/activate  # Activate venv
```

**Development Commands:**
```bash
# Run Python scripts
venv/bin/python script.py  # or bazel run //:script

# Web app development
bazel run //apps/hyd:next_dev  # or pnpm dev from app directory

# Embedded builds
bazel build //emb/project/robo24:robo24_pico.bin

# Container builds and deployment
bazel run //apps/hyd:hyd_amd64_load  # Load to local Docker
bazel run //apps/hyd:hyd_push  # Push to GCR
```

## Project-Specific Patterns

### Sharetrace Exception Handling
The `nlb.sharetrace` module captures rich exception data including nested exceptions, Git context, and code snippets:
```python
from nlb.sharetrace import install_exception_hook
install_exception_hook()  # Call early in main()
# Generates JSON cache files, visualize with `sharetrace` CLI
```

### Bazel Custom Macros
- `cc_unittest()` in `bzl/macros/cc.bzl` - C++ tests with platform transitions
- `js_image()` - Next.js containerization with proper layer caching
- Custom embedded firmware rules for Pico projects

### Service Architecture
Services use Tailscale sidecars for TLS and networking. Each service gets a `*.barn-arcturus.ts.net` domain. Database services typically pair with application containers via Docker Compose.

### Multi-Language Integration
- Python packages importable as `from nlb.package import module`
- TypeScript/Next.js apps in `apps/` with shared dependencies in workspace
- C++ embedded code with Bazel transitions between host and embedded platforms
- Rust WASM modules built with `rules_rust`

## Key Files to Reference
- `MODULE.bazel` - Central dependency management for all languages
- `requirements.txt` & `pyproject.toml` - Python dependency specification
- `bzl/macros/` - Custom build patterns and abstractions
- `services/docker-compose.*.yaml` - Service deployment patterns
- `setup.sh` - Complete development environment bootstrap

## Development Tips
- Always use absolute paths with Bazel: `//path/to:target`
- Embedded work requires udev rules from `misc/udev/` for device access
- Database services need password files in `services/secrets/`
