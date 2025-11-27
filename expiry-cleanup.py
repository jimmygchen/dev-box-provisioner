#!/usr/bin/env python3
"""Delete servers that have passed their expiry date"""
import subprocess
import json
from datetime import datetime


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    print(f"Running expiry cleanup at {datetime.utcnow()} UTC")

    # Get all servers with managed-by label
    ret, stdout, _ = run_cmd("hcloud server list -o json -l managed-by=dev-box-provisioner")
    if ret != 0 or not stdout:
        print("No managed servers found")
        return

    servers = json.loads(stdout)
    today_utc = datetime.utcnow().date()
    deleted_count = 0

    for server in servers:
        name = server.get('name')
        labels = server.get('labels', {})
        expires = labels.get('expires')

        if not expires:
            print(f"Warning: {name} has no expiry label, skipping")
            continue

        try:
            expiry_date = datetime.strptime(expires, '%Y-%m-%d').date()
        except ValueError:
            print(f"Warning: {name} has invalid expiry date '{expires}', skipping")
            continue

        if expiry_date < today_utc:
            print(f"\n=== Deleting: {name} ===")
            print(f"Expired on {expires}")

            ret, _, stderr = run_cmd(f"hcloud server delete {server['id']}")
            if ret != 0:
                print(f"ERROR: Failed to delete server: {stderr}")
                continue

            print(f"✓ Deleted server")

            # Delete associated SSH key by label
            ret, stdout, _ = run_cmd(f"hcloud ssh-key list -o noheader -o columns=name -l server={name}")
            if stdout:
                for key_name in stdout.split('\n'):
                    if key_name:
                        run_cmd(f"hcloud ssh-key delete '{key_name}'")
                print(f"✓ Deleted SSH key(s)")

            deleted_count += 1
        else:
            print(f"{name}: expires {expires} (still valid)")

    print(f"\nDeleted {deleted_count} expired server(s)")


if __name__ == "__main__":
    main()
