#!/usr/bin/env python3
"""Provision dev boxes on Hetzner Cloud from dev_boxes.yml"""
import yaml
import subprocess
import sys
import re
import json
import argparse


def run_cmd(cmd, dry_run=False):
    if dry_run:
        print(f"  [DRY-RUN] Would execute: {cmd}")
        return 0, "", ""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_valid_identifier(value):
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', value))


def is_valid_date(value):
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(value)))


def main():
    parser = argparse.ArgumentParser(description='Provision dev boxes on Hetzner Cloud')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without creating servers')
    args = parser.parse_args()

    if args.dry_run:
        print("=" * 60)
        print("DRY-RUN MODE - No servers will be created")
        print("=" * 60)

    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
            server_type = config.get('server_type', 'cpx52')
            location = config.get('location', 'hel1')
            image = config.get('image', 'ubuntu-24.04')
            max_servers = config.get('max_servers', 10)
    except Exception as e:
        print(f"Error reading config.yml: {e}")
        sys.exit(1)

    print(f"Config: {server_type} @ {location}, {image}, max={max_servers}")

    # Verify cloud-init.yaml exists
    try:
        with open('cloud-init.yaml', 'r') as f:
            pass
    except FileNotFoundError:
        print("ERROR: cloud-init.yaml not found")
        sys.exit(1)

    try:
        with open('dev_boxes.yml', 'r') as f:
            data = yaml.safe_load(f)
            if not data:
                print("No dev boxes defined")
                sys.exit(0)
    except Exception as e:
        print(f"Error reading dev_boxes.yml: {e}")
        sys.exit(1)

    if len(data) > max_servers:
        print(f"ERROR: {len(data)} servers requested, max is {max_servers}")
        print(f"Increase 'max_servers' in config.yml if needed")
        sys.exit(1)

    print(f"\nProcessing {len(data)} dev box(es)...")

    for box in data:
        key = box.get('key')
        name = box.get('name')
        until = box.get('until')

        # YAML may parse dates as date objects, convert to string
        if until and not isinstance(until, str):
            until = str(until)

        if not all([key, name, until]):
            print(f"Skipping invalid entry: {box}")
            continue

        if not is_valid_identifier(key):
            print(f"ERROR: Invalid key '{key}' (alphanumeric, dash, underscore only)")
            continue

        if not is_valid_identifier(name):
            print(f"ERROR: Invalid name '{name}' (alphanumeric, dash, underscore only)")
            continue

        if not is_valid_date(until):
            print(f"ERROR: Invalid date '{until}' (must be YYYY-MM-DD)")
            continue

        print(f"\n=== {name} (user: {key}) ===")

        ret, stdout, _ = run_cmd(f"hcloud server list -o noheader -o columns=name | grep -x '{name}' || true", dry_run=args.dry_run)
        if stdout and not args.dry_run:
            print(f"Already exists, skipping")
            continue

        print(f"Fetching SSH keys from github.com/{key}.keys")
        ret, ssh_keys, _ = run_cmd(f"curl -sf https://github.com/{key}.keys", dry_run=args.dry_run)
        if not args.dry_run and (ret != 0 or not ssh_keys):
            print(f"ERROR: Could not fetch SSH keys")
            continue

        if args.dry_run:
            ssh_keys = "ssh-rsa FAKE_KEY"

        ssh_key_name = f"{key}-github-key"
        ret, existing_key, _ = run_cmd(f"hcloud ssh-key list -o noheader -o columns=name | grep -x '{ssh_key_name}' || true", dry_run=args.dry_run)

        if not existing_key:
            print(f"Adding SSH key: {ssh_key_name}")
            first_key = ssh_keys.split('\n')[0]
            ret, _, stderr = run_cmd(f"hcloud ssh-key create --name '{ssh_key_name}' --public-key '{first_key}'", dry_run=args.dry_run)
            if ret != 0:
                print(f"ERROR: Failed to create SSH key: {stderr}")
                continue

        print(f"Creating server: {name}")

        if args.dry_run:
            print(f"  [DRY-RUN] Config: {server_type}, {location}, {image}")
            print(f"  [DRY-RUN] Labels: owner={key}, expires={until}")

            ret, _, _ = run_cmd(f"hcloud server-type describe {server_type}", dry_run=False)
            print(f"  [DRY-RUN] Server type: {'✓' if ret == 0 else '✗ INVALID'}")

            ret, _, _ = run_cmd(f"hcloud location describe {location}", dry_run=False)
            print(f"  [DRY-RUN] Location: {'✓' if ret == 0 else '✗ INVALID'}")
        else:
            create_cmd = f"""hcloud server create \\
              --name '{name}' \\
              --type {server_type} \\
              --location {location} \\
              --image {image} \\
              --ssh-key '{ssh_key_name}' \\
              --user-data-from-file cloud-init.yaml \\
              --label managed-by=dev-box-provisioner \\
              --label owner={key} \\
              --label expires={until}"""

            ret, stdout, stderr = run_cmd(create_cmd, dry_run=False)
            if ret != 0:
                print(f"ERROR: {stderr}")
                continue

            print(f"✓ Created")

            # Get server details to show IP
            server_id = None
            parts = stdout.split()
            if len(parts) >= 2 and parts[1].isdigit():
                server_id = parts[1]

            if server_id:
                ret, server_info, _ = run_cmd(f"hcloud server describe {server_id} -o json", dry_run=False)
                if ret == 0:
                    info = json.loads(server_info)
                    ip = info.get('public_net', {}).get('ipv4', {}).get('ip')
                    if ip:
                        print(f"  IP: {ip}")
                        print(f"  SSH: ssh root@{ip}")
                        print(f"  Watch provisioning: tail -f /var/log/cloud-init.log")


if __name__ == "__main__":
    main()
