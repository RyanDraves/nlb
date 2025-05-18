FROM ubuntu:noble

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    make \
    cmake \
    patch \
    bash \
    curl \
    zip \
    unzip \
    portaudio19-dev \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.source=https://github.com/RyanDraves/nlb
LABEL org.opencontainers.image.description="Environment image"
LABEL org.opencontainers.image.licenses=MIT
