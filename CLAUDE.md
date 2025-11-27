# Development Guidelines

## Code Style & Principles

### Simplicity First
- Keep code simple, concise, and readable
- Avoid over-engineering and premature abstraction
- No verbose comments - code should be self-explanatory
- Remove unnecessary complexity

### Comments & Documentation
- Minimal inline comments
- Short, direct error messages with parenthetical hints
- Avoid redundant explanations of obvious code
- Keep configuration comments brief

### Security & Safety
- Input validation to prevent command injection
- Cost controls with configurable limits
- Idempotent operations (safe to re-run)
- Minimal log exposure (don't leak sensitive data)

### Configuration Management
- Externalize all configuration to `config.yml`
- No hardcoded values in scripts
- Keep YAML files clean and minimal

### Development Workflow
- Branch protection requires PR review
- No manual approval workflows (minimal friction)
- Test locally with dry-run mode first
- Use virtual environments for Python dependencies
- No Claude attribution in commit messages

## Architecture Approach

### Infrastructure as Code
- Dev boxes defined in version-controlled YAML
- GitHub Actions for automation
- Transparent - everyone sees what's running
- Self-service without direct cloud access
- Compare actual resources (Hetzner API) vs desired state (YAML) - not git diffs
- Delete what exists in cloud but not in YAML

### Cost Optimization
- On-demand provisioning (pay only for usage)
- Expiry dates to prevent forgotten resources
- Safety limits to prevent accidental mass creation
- Reasonable defaults for server specs

## Testing
- Always provide dry-run mode for safe testing
- Validate configuration against real APIs when possible
- Local testing should mirror CI/CD behavior
- Keep dependencies minimal (requirements.txt)
