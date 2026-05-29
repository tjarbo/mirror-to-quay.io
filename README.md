# mirror-to-quay.io

Automates selective container image replication to **quay.io**. Define the
images and tags you want to mirror in a simple YAML config file, and let the
automation handle the rest – either on a schedule via GitHub Actions or locally
with Docker / Podman.

## Quick start

### Prerequisites

- Python 3 with `pyyaml` (`pip install pyyaml`)
- **Docker** or **Podman** installed and available on `PATH`
- Logged in to `quay.io` (for pushing)

### Configuration

Edit `mirror-config.yaml` to define the images to mirror:

```yaml
images:
  - source: ghcr.io/pocket-id/pocket-id
    destination: quay.io/tjarbo/pocket-id
    tags:
      - v2
      - latest
```

Each entry specifies a `source` image, a `destination` on quay.io, and one or
more `tags` to replicate.

### Run locally

```bash
# Mirror all images from the config file
python mirror.py config

# Use a custom config file
python mirror.py config -f path/to/config.yaml

# Mirror a single image ad-hoc
python mirror.py adhoc ghcr.io/org/image:tag quay.io/org/image:tag
```

The script auto-detects whether to use Docker or Podman (Docker takes
precedence).

## GitHub Actions

### Scheduled mirroring (`.github/workflows/mirror.yml`)

Runs every day at 06:00 UTC and mirrors all images defined in
`mirror-config.yaml`. Can also be triggered manually from the Actions tab.

### Ad-hoc mirroring (`.github/workflows/mirror-adhoc.yml`)

Trigger manually from the Actions tab. Provide:

| Input | Description | Example |
|---|---|---|
| `source` | Full source image reference | `ghcr.io/org/image:tag` |
| `destination` | Full destination image reference | `quay.io/org/image:tag` |

## Setup

1. Create the following **repository secrets**:
   - `QUAY_USERNAME`
   - `QUAY_PASSWORD`
2. Ensure the Quay.io account has push access to the destination repositories.
