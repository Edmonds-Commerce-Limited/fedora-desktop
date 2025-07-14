# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Ansible-based automation project for setting up Fedora desktop environments. It uses a modular playbook structure with optional components for different use cases.

## Common Development Commands

### Running the Main Setup
```bash
# Full automated setup from fresh Fedora install
source <(curl -sS https://raw.githubusercontent.com/LongTermSupport/fedora-desktop/main/run.bash)

# Run main playbook locally (after initial setup)
ansible-playbook ./playbooks/playbook-main.yml

# Run with vault password (for encrypted variables)
ansible-playbook ./playbooks/playbook-main.yml --vault-password-file=./untracked/.vault-password
```

### Running Optional Playbooks
```bash
# Install Flatpaks
ansible-playbook ./playbooks/imports/play-install-flatpaks.yml

# Run specific optional playbook from common tools
ansible-playbook ./playbooks/imports/optional/common/play-docker.yml

# Run hardware-specific playbook
ansible-playbook ./playbooks/imports/optional/hardware-specific/play-displaylink.yml
```

### Testing and Validation
```bash
# Check syntax without running
ansible-playbook ./playbooks/playbook-main.yml --syntax-check

# Dry run to see what would change
ansible-playbook ./playbooks/playbook-main.yml --check

# Run with increased verbosity for debugging
ansible-playbook ./playbooks/playbook-main.yml -vvv

# Validate specific playbook
ansible-playbook ./playbooks/imports/play-basic-configs.yml --check
```

### Ansible Galaxy Dependencies
```bash
# Install required collections
ansible-galaxy collection install -r requirements.yml

# Force reinstall collections
ansible-galaxy collection install -r requirements.yml --force
```

## High-Level Architecture

### Directory Structure
- **`playbooks/`** - All Ansible playbooks organized by purpose
  - **`playbook-main.yml`** - Main orchestrator that imports other playbooks in sequence
  - **`imports/`** - Core playbooks always run during setup
  - **`imports/optional/`** - Optional components organized by category:
    - **`common/`** - Development tools, applications, utilities
    - **`experimental/`** - Features under development or testing
    - **`hardware-specific/`** - Hardware-specific configurations (NVIDIA, DisplayLink, etc.)

### Key Architectural Decisions
1. **No Traditional Roles**: Uses playbook imports instead of Ansible roles for simpler structure
2. **Local Execution**: Configured for localhost only (no SSH transport)
3. **Modular Design**: Each playbook is self-contained and can be run independently
4. **Version Targeting**: Currently targets Fedora 40 specifically (validated in preflight checks)
5. **Fact Caching**: Facts cached in `./untracked/facts/` to improve performance

### Configuration Management
- **`ansible.cfg`** - Core Ansible settings (callback plugins, paths, transport)
- **`environment/localhost/`** - Inventory and host variables
- **`host_vars/localhost.yml`** - User-specific variables (created from `.dist` template)
- **Vault Support**: Sensitive data encrypted with ansible-vault

### Important Patterns
1. **Task Organization**: Tasks use consistent naming: `"<Component> | <Action> | <Details>"`
2. **Variable Naming**: Uses underscore_case for all variables
3. **Conditionals**: Frequently checks `ansible_distribution_major_version` for Fedora version
4. **Package Management**: Uses `dnf` module for system packages, dedicated playbooks for Flatpaks
5. **User Context**: Most tasks run as the regular user, with `become: true` only when needed

### Common Development Tasks
When modifying playbooks:
1. Always validate syntax before running: `--syntax-check`
2. Use `--check` mode to preview changes
3. Test individual playbooks in isolation before adding to main
4. Keep optional components in appropriate subdirectories
5. Document any new variables in the `.dist` template files

### Testing Approach
The project uses manual testing approach:
- Syntax validation via `--syntax-check`
- Dry runs with `--check` flag
- Fresh VM testing for full setup validation
- No automated test suite currently exists