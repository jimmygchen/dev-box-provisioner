#!/usr/bin/env python3
"""Delete servers for entries removed from dev_boxes.yml"""
import yaml
import subprocess
import sys


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_previous_boxes():
    """Get dev_boxes.yml from previous commit"""
    ret, stdout, _ = run_cmd("git show HEAD:dev_boxes.yml 2>/dev/null")
    if ret != 0:
        return []
    try:
        data = yaml.safe_load(stdout)
        return data if data else []
    except:
        return []


def get_current_boxes():
    """Get current dev_boxes.yml"""
    try:
        with open('dev_boxes.yml', 'r') as f:
            data = yaml.safe_load(f)
            return data if data else []
    except:
        return []


def main():
    previous = get_previous_boxes()
    current = get_current_boxes()

    # Build sets of server names
    previous_names = {box.get('name') for box in previous if box.get('name')}
    current_names = {box.get('name') for box in current if box.get('name')}

    # Find deleted entries
    deleted = previous_names - current_names

    if not deleted:
        print("No servers to delete")
        return

    print(f"Found {len(deleted)} server(s) to delete")

    for name in deleted:
        print(f"\n=== Deleting: {name} ===")

        # Check if server exists
        ret, stdout, _ = run_cmd(f"hcloud server list -o noheader -o columns=name | grep -x '{name}' || true")
        if not stdout:
            print(f"Server '{name}' not found, skipping")
        else:
            # Delete the server
            ret, stdout, stderr = run_cmd(f"hcloud server delete '{name}'")
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


if __name__ == "__main__":
    main()
