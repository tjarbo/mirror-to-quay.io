#!/usr/bin/env python3
"""Mirror container images to quay.io.

Supports two modes:
  1. Config mode  – reads a YAML config file and mirrors every image/tag pair.
  2. Ad-hoc mode  – mirrors a single source image:tag to a destination image:tag.

The script auto-detects whether to use *docker* or *podman* (docker takes
precedence).
"""

import argparse
import shutil
import subprocess
import sys
import yaml


def detect_runtime():
    """Return the container runtime binary name (docker preferred)."""
    for cmd in ("docker", "podman"):
        if shutil.which(cmd):
            return cmd
    print("Error: neither docker nor podman found on PATH", file=sys.stderr)
    sys.exit(1)


def run(cmd):
    """Run a shell command, stream output, and abort on failure."""
    print(f"+ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error: command failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def mirror_image(runtime, source, destination):
    """Pull source, tag as destination, and push."""
    print(f"\n>>> Mirroring {source} -> {destination}")
    run([runtime, "pull", source])
    run([runtime, "tag", source, destination])
    run([runtime, "push", destination])


def load_config(path):
    """Load and validate the YAML config file."""
    with open(path) as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict) or "images" not in cfg:
        print("Error: config file must contain an 'images' list", file=sys.stderr)
        sys.exit(1)

    return cfg["images"]


def mirror_from_config(runtime, config_path):
    """Mirror all images defined in a configuration file."""
    images = load_config(config_path)
    errors = []
    for entry in images:
        source_repo = entry["source"]
        destination_repo = entry["destination"]
        for tag in entry.get("tags", []):
            source = f"{source_repo}:{tag}"
            destination = f"{destination_repo}:{tag}"
            try:
                mirror_image(runtime, source, destination)
            except SystemExit:
                errors.append(f"{source} -> {destination}")
                print(f"Warning: failed to mirror {source}, continuing…", file=sys.stderr)

    if errors:
        print(f"\nFailed to mirror {len(errors)} image(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Mirror container images to quay.io")
    sub = parser.add_subparsers(dest="command", required=True)

    # Config-based mirroring
    cfg_parser = sub.add_parser("config", help="Mirror images defined in a config file")
    cfg_parser.add_argument(
        "-f", "--file",
        default="mirror-config.yaml",
        help="Path to the YAML config file (default: mirror-config.yaml)",
    )

    # Ad-hoc single image mirroring
    adhoc_parser = sub.add_parser("adhoc", help="Mirror a single image")
    adhoc_parser.add_argument("source", help="Full source image reference (e.g. ghcr.io/org/img:tag)")
    adhoc_parser.add_argument("destination", help="Full destination image reference (e.g. quay.io/org/img:tag)")

    args = parser.parse_args()
    runtime = detect_runtime()
    print(f"Using container runtime: {runtime}")

    if args.command == "config":
        mirror_from_config(runtime, args.file)
    elif args.command == "adhoc":
        mirror_image(runtime, args.source, args.destination)

    print("\nDone.")


if __name__ == "__main__":
    main()
