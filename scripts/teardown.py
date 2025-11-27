#!/usr/bin/env python3
"""Delete managed servers not in dev_boxes.yml"""
import yaml
import subprocess
import sys
import json


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    # Get current dev_boxes.yml
    try:
        with open('dev_boxes.yml', 'r') as f:
            data = yaml.safe_load(f)
            current_names = {box.get('name') for box in (data or []) if box.get('name')}
    except Exception as e:
        print(f"ERROR: Could not read dev_boxes.yml: {e}")
        sys.exit(1)

    print(f"Current dev_boxes.yml has {len(current_names)} server(s)")

    # Get all managed servers from Hetzner
    ret, stdout, _ = run_cmd("hcloud server list -o json -l managed-by=dev-box-provisioner")
    if ret != 0 or not stdout:
        print("No managed servers found in Hetzner")
        return

    servers = json.loads(stdout)
    managed_names = {s.get('name') for s in servers if s.get('name')}

    print(f"Found {len(managed_names)} managed server(s) in Hetzner")

    # Find servers to delete (in Hetzner but not in YAML)
    to_delete = managed_names - current_names

    if not to_delete:
        print("No servers to delete")
        return

    print(f"Deleting {len(to_delete)} server(s) not in dev_boxes.yml")

    for name in to_delete:
        print(f"\n=== Deleting: {name} ===")

        # Delete the server
        ret, _, stderr = run_cmd(f"hcloud server delete '{name}'")
        if ret != 0:
            print(f"ERROR: Failed to delete server: {stderr}")
            continue
        print(f"✓ Deleted server")

    # Note: SSH keys are shared across user's servers, not deleted here
    # Use manual cleanup workflow or wait for user to have no servers


if __name__ == "__main__":
    main()
