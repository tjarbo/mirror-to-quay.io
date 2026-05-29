# Agents

This document describes how AI agents should interact with this repository.

## Repository overview

This repository automates selective container image mirroring to quay.io.
A Python script (`mirror.py`) handles the core logic; GitHub Actions workflows
handle scheduling, authentication, and triggering.

## Key files

| File | Purpose |
|---|---|
| `mirror.py` | Core mirroring script (supports docker & podman) |
| `mirror-config.yaml` | Defines which images and tags to mirror |
| `.github/workflows/mirror.yml` | Scheduled / manual config-based mirroring |
| `.github/workflows/mirror-adhoc.yml` | Manual ad-hoc single-image mirroring |

## Working with the code

- **Language**: Python 3 (single script, no package structure).
- **Dependencies**: `pyyaml` (install via `pip install pyyaml`).
- **No build step** – the script runs directly.
- **No test suite** – validate changes by running `python mirror.py --help`.

## Conventions

- Keep `mirror.py` as a single self-contained script.
- Docker is the preferred runtime; podman is the fallback.
- The only supported destination registry is **quay.io**.
- Do not modify destination registries – they are pre-configured.
- Credentials (`QUAY_USERNAME`, `QUAY_PASSWORD`) are stored as GitHub repository secrets.
