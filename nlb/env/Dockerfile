FROM ubuntu:noble

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    patch \
    bash \
    curl \
    zip \
    unzip \
    portaudio19-dev \
    python3 \
    wget \
    # Non-hermetic compiler due to issues finding `ld` with picotool's toolchain
    # while using remote execution
    gcc-arm-none-eabi \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.source=https://github.com/RyanDraves/nlb
LABEL org.opencontainers.image.description="Environment image"
LABEL org.opencontainers.image.licenses=MIT
