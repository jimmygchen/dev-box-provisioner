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

5. **Start working**:
   - Lighthouse is already cloned in `~/lighthouse`
   - Build with `cd ~/lighthouse && make`
   - Run Kurtosis tests directly with `kurtosis` command
   - All dev tools pre-installed and ready to use

## Server Specifications

- **Type**: cpx52 (16 vCPU, 32GB RAM, AMD, dedicated cores)
- **OS**: Ubuntu 24.04
- **Region**: hel1 (Helsinki, Finland - eu-central)
- **Pre-installed**: Docker, Rust, GitHub CLI, Kurtosis, build tools, Zsh with Oh My Zsh
- **Pre-cloned**: Lighthouse repository in `~/lighthouse`

Server type and location are configured in `config.yml` and apply globally to all machines.

## Safety Features

- **Max server limit**: Maximum of 10 servers can be provisioned at once (configurable in `config.yml`)
- **Input validation**: All user inputs are validated to prevent command injection attacks
- **Idempotent operations**: Re-running provisioning won't create duplicate servers
- **Minimal log exposure**: Server IPs and sensitive details are not logged to GitHub Actions

## Current Limitations

- Server type and location are global (no per-machine override)
- Hetzner project is determined by API token scope (token must be created within the target project)
- Maximum 10 servers can exist at once (safety limit to prevent cost overruns)

## TODO

### Nice to Have
- [ ] **List running machines**: Command/action to list all currently provisioned servers
- [ ] **Notification**: Post server IP and connection details as PR comment
- [ ] **Custom server types**: Allow per-machine server type override
- [ ] **Cost tracking**: Report estimated costs in PR comments
- [ ] **GitHub environments**: Use GitHub Environments for manual approval before provisioning
- [ ] **Project selection**: Support specifying which Hetzner project to use (current approach: scope API token to specific project)

## Setup

### Required GitHub Secrets

1. `HETZNER_API_TOKEN`: Your Hetzner Cloud API token
   - Create at: https://console.hetzner.cloud/ → Select your project → Security → API Tokens
   - Needs read/write access to servers and SSH keys
   - **Recommended**: Create a dedicated project for dev boxes with resource quotas, then generate the API token for that project only. This ensures the token can only create resources in that specific project, providing automatic cost control and isolation.

### SSH Keys

Your SSH public keys are automatically fetched from `https://github.com/<username>.keys`. Make sure you have at least one SSH key added to your GitHub account:
- Go to GitHub Settings → SSH and GPG keys
- Add your public key if not already present

## How It Works

### Provisioning (on push to main)
1. Workflow triggers on any push to main branch
2. **Teardown phase**: Compares managed servers in Hetzner vs `dev_boxes.yml`, deletes any not in YAML
3. **Provision phase**: For each entry in the YAML:
   - Check if expiry date has passed (skip if expired)
   - Check if a server with that name already exists (idempotent)
   - Fetch the user's SSH keys from GitHub
   - Add SSH key to Hetzner if not already present (one key per user, reused across servers)
   - Create server with cloud-init configuration
   - Label server with metadata (owner, expiry date, managed-by tag)
4. The server boots and runs cloud-init to install all tools
5. User can SSH in and start working

### Expiry Cleanup (daily at midnight UTC)
- Automatically runs daily to check all managed servers
- Deletes servers where expiry date has passed
- Can be manually triggered from GitHub Actions tab
- Expiry dates are inclusive (server valid until end of the specified date)

**To delete a server**: Remove its entry from `dev_boxes.yml` and merge the PR (immediate deletion).
**For automatic deletion**: Server will be deleted at midnight UTC after the expiry date.

## Contributing

Improvements welcome! Particularly for items in the TODO section.
