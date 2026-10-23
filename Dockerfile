# syntax=docker/dockerfile:1
FROM ubuntu:24.04

# Avoid interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install BCC, Python 3, kernel tracing tools, kmod, xz-utils, and Docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-bpfcc \
    bpfcc-tools \
    python3-networkx \
    python3-docker \
    docker.io \
    iproute2 \
    kmod \
    xz-utils \
    tar \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY . /app

# Entrypoint runs the controller in live eBPF mode by default
CMD ["python3", "-u", "controller.py"]
