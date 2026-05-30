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


def parse_image_ref(ref):
    """Split an image reference into (repository, tag).

    If no tag is present after the last ':', the tag defaults to 'latest'.
    """
    # Handle images with digest (@sha256:...) – strip the digest
    if "@" in ref:
        ref = ref.split("@")[0]

    # The tag follows the last ':' but only when that ':' is not part of a port
    # number.  A port appears right after the host (first component) and is
    # always numeric, so we look for ':' after the last '/'.
    last_slash = ref.rfind("/")
    colon = ref.rfind(":")
    if colon > last_slash and last_slash != -1:
        return ref[:colon], ref[colon + 1:]
    # No tag found
    return ref, "latest"


def update_config(config_path, source, destination):
    """Add an image/tag pair to the YAML config file.

    If an entry with the same source and destination repository already exists,
    the tag is appended (unless it is already listed).  Otherwise a new entry
    is created.

    Returns True if the config was modified, False if nothing changed.
    """
    source_repo, source_tag = parse_image_ref(source)
    dest_repo, dest_tag = parse_image_ref(destination)

    try:
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        cfg = {}

    images = cfg.setdefault("images", [])

    # Look for an existing entry with matching repos
    for entry in images:
        if entry.get("source") == source_repo and entry.get("destination") == dest_repo:
            tags = entry.setdefault("tags", [])
            if source_tag in tags:
                print(f"Tag '{source_tag}' already exists for {source_repo} -> {dest_repo}, skipping.")
                return False
            tags.append(source_tag)
            print(f"Added tag '{source_tag}' to existing entry {source_repo} -> {dest_repo}.")
            break
    else:
        # No matching entry – create a new one
        images.append({
            "source": source_repo,
            "destination": dest_repo,
            "tags": [source_tag],
        })
        print(f"Added new entry {source_repo}:{source_tag} -> {dest_repo}:{dest_tag}.")

    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

    return True


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

    # Update config file with a new image/tag
    update_parser = sub.add_parser("update-config", help="Add an image to the config file")
    update_parser.add_argument("source", help="Full source image reference (e.g. ghcr.io/org/img:tag)")
    update_parser.add_argument("destination", help="Full destination image reference (e.g. quay.io/org/img:tag)")
    update_parser.add_argument(
        "-f", "--file",
        default="mirror-config.yaml",
        help="Path to the YAML config file (default: mirror-config.yaml)",
    )

    args = parser.parse_args()

    if args.command == "update-config":
        changed = update_config(args.file, args.source, args.destination)
        if not changed:
            print("\nConfig unchanged.")
        else:
            print("\nConfig updated.")
        return

    runtime = detect_runtime()
    print(f"Using container runtime: {runtime}")

    if args.command == "config":
        mirror_from_config(runtime, args.file)
    elif args.command == "adhoc":
        mirror_image(runtime, args.source, args.destination)

    print("\nDone.")


if __name__ == "__main__":
    main()
