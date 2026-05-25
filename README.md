# mirror-pocket-id-to-quay.io

Mirrors `ghcr.io/pocket-id/pocket-id` to `quay.io/tjarbo/pocket-id` so the image can be pulled from a registry with IPv6 support.

## Setup

1. Create the following repository secrets:
   - `QUAY_USERNAME`
   - `QUAY_PASSWORD`
2. Ensure the Quay account can push to `quay.io/tjarbo/pocket-id`.

## Usage

The workflow is defined in `.github/workflows/mirror.yml` and supports two triggers:

- **Scheduled**: Runs every day in the morning and mirrors tag `v2`.
- **Manual** (`workflow_dispatch`): Optional input `image_tag` (defaults to `v2`).

Manual run examples:

- Leave `image_tag` empty to mirror `v2`
- Set `image_tag` to `v3` to mirror `ghcr.io/pocket-id/pocket-id:v3`
