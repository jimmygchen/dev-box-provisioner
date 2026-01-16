#!/usr/bin/env python3
"""Delete managed servers not in dev_boxes.yml or expired"""
import yaml
import subprocess
import sys
import json
from datetime import datetime, timezone


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    # Get current dev_boxes.yml
    try:
        with open('dev_boxes.yml', 'r') as f:
            data = yaml.safe_load(f) or []
            boxes_by_name = {}
            for box in data:
                name = box.get('name')
                if name:
                    until = box.get('until')
                    if until and not isinstance(until, str):
                        until = str(until)
                    boxes_by_name[name] = until
    except Exception as e:
        print(f"ERROR: Could not read dev_boxes.yml: {e}")
        sys.exit(1)

    print(f"Current dev_boxes.yml has {len(boxes_by_name)} server(s)")

    # Get all managed servers from Hetzner
    ret, stdout, _ = run_cmd("hcloud server list -o json -l managed-by=dev-box-provisioner")
    if ret != 0 or not stdout:
        print("No managed servers found in Hetzner")
        return

    servers = json.loads(stdout)
    managed_names = {s.get('name') for s in servers if s.get('name')}

    print(f"Found {len(managed_names)} managed server(s) in Hetzner")

    today_utc = datetime.now(timezone.utc).date()
    to_delete = []

    for name in managed_names:
        if name not in boxes_by_name:
            to_delete.append((name, "not in YAML"))
        else:
            until = boxes_by_name[name]
            if until:
                try:
                    expiry_date = datetime.strptime(until, '%Y-%m-%d').date()
                    if expiry_date < today_utc:
                        to_delete.append((name, f"expired on {until}"))
                except ValueError:
                    pass

    if not to_delete:
        print("No servers to delete")
        return

    print(f"Deleting {len(to_delete)} server(s)")

    for name, reason in to_delete:
        print(f"\n=== Deleting: {name} ({reason}) ===")

        ret, _, stderr = run_cmd(f"hcloud server delete '{name}'")
        if ret != 0:
            print(f"ERROR: Failed to delete server: {stderr}")
            continue
        print(f"✓ Deleted server")

    # Note: SSH keys are shared across user's servers, not deleted here
    # Use manual cleanup workflow or wait for user to have no servers


if __name__ == "__main__":
    main()
