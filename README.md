# Dev Box Provisioner

Automated on-demand Hetzner server provisioning for development work, managed via pull requests.

## Overview

This repository automates the creation of development servers on Hetzner Cloud. Instead of manually creating and configuring servers, developers can simply create a pull request to request a dev box. Once merged, a GitHub Action automatically provisions the server with all necessary tools pre-installed.

## Why?

- **Cost-effective**: Pay only for what you use. A day of development on cpx52 costs ~€0.50
- **Time-saving**: No manual setup required - servers come pre-configured with Docker, Rust, GitHub CLI, Kurtosis, and more
- **Transparent**: All dev boxes are tracked in `dev_boxes.yml` - everyone knows what's running
- **Self-service**: Developers can request machines without needing Hetzner access
- **Automatic cleanup**: Expiry dates prevent forgotten machines from racking up costs

## How to Request a Dev Box

1. **Edit `dev_boxes.yml`** and add your entry:
   ```yaml
   - key: your-github-username
     name: unique-machine-name
     until: 2025-12-31
   ```

   - `key`: Your GitHub username (used to fetch your SSH public keys)
   - `name`: Unique name for your machine (e.g., `yourname-feature-work`)
   - `until`: Expiry date in YYYY-MM-DD format

2. **Create a pull request** with your changes

3. **Once merged**, the GitHub Action will:
   - Fetch your SSH public keys from `https://github.com/your-username.keys`
   - Add them to Hetzner
   - Create your server with the specified configuration
   - Provision it with all development tools via cloud-init

4. **Connect to your server**:
   ```bash
   ssh root@<server-ip>
   ```

   You can find the server IP in the GitHub Actions logs or via Hetzner Cloud Console.

## Server Specifications

- **Type**: cpx52 (16 vCPU, 32GB RAM, AMD, dedicated cores)
- **OS**: Ubuntu 24.04
- **Region**: hel1 (Helsinki, Finland - eu-central)
- **Pre-installed**: Docker, Rust, GitHub CLI, Kurtosis, build tools, Zsh with Oh My Zsh

Server type and location are configured in `config.yml` and apply globally to all machines.

## Safety Features

- **Max server limit**: Maximum of 10 servers can be provisioned at once (configurable in `config.yml`)
- **Input validation**: All user inputs are validated to prevent command injection attacks
- **Idempotent operations**: Re-running provisioning won't create duplicate servers
- **Minimal log exposure**: Server IPs and sensitive details are not logged to GitHub Actions

## Current Limitations

- Server type and location are global (no per-machine override)
- All servers use the default Hetzner project
- Manual deletion required - remove your entry from `dev_boxes.yml` and the automation doesn't tear it down yet
- Maximum 10 servers can exist at once (safety limit to prevent cost overruns)

## TODO

### High Priority
- [ ] **Teardown deleted machines**: Detect when entries are removed from `dev_boxes.yml` and delete corresponding servers
- [ ] **Daily expiry cleanup**: Scheduled GitHub Action to check `until` dates and delete expired servers
- [ ] **Project selection**: Support specifying which Hetzner project to create servers in (not default)

### Nice to Have
- [ ] **List running machines**: Command/action to list all currently provisioned servers
- [ ] **Notification**: Post server IP and connection details as PR comment
- [ ] **Custom server types**: Allow per-machine server type override
- [ ] **Cost tracking**: Report estimated costs in PR comments
- [ ] **GitHub environments**: Use GitHub Environments for manual approval before provisioning

## Setup

### Required GitHub Secrets

1. `HETZNER_API_TOKEN`: Your Hetzner Cloud API token
   - Create at: https://console.hetzner.cloud/
   - Needs read/write access to servers and SSH keys

### SSH Keys

Your SSH public keys are automatically fetched from `https://github.com/<username>.keys`. Make sure you have at least one SSH key added to your GitHub account:
- Go to GitHub Settings → SSH and GPG keys
- Add your public key if not already present

## How It Works

1. When a PR is merged that modifies `dev_boxes.yml`, the workflow triggers
2. For each entry in the YAML:
   - Check if a server with that name already exists (idempotent)
   - Fetch the user's SSH keys from GitHub
   - Add SSH key to Hetzner if not already present
   - Create server with cloud-init configuration
   - Label server with metadata (owner, expiry date, managed-by tag)
3. The server boots and runs cloud-init to install all tools
4. User can SSH in and start working

## Contributing

Improvements welcome! Particularly for items in the TODO section.
