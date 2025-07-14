# Container Management with Ansible (Incus/LXD)

This environment allows you to manage Incus or LXD containers using Ansible.

## Backwards Compatibility

This inventory script automatically detects whether you're using:
- **Incus** (preferred for newer Fedora versions)
- **LXC/LXD** (for older Fedora versions)

## How it Works

- **Dynamic Inventory**: The `incus_inventory.py` script automatically discovers all containers
- **Automatic Grouping**: Containers are grouped by:
  - Status: `running`, `stopped`
  - OS: `ubuntu`, `fedora`, `alpine` (based on image)
  - All containers: `containers` (with aliases `incus_containers` and `lxc_containers`)
- **SSH Connection**: Uses SSH with the appropriate key:
  - `~/.ssh/id_incus` for Incus setups
  - `~/.ssh/id_lxc` for LXC/LXD setups

## Usage

### 1. List all containers in inventory
```bash
cd environment/lxc
ansible-inventory --list
```

### 2. Test connectivity to all running containers
```bash
ansible running -m ping
```

### 3. Run ad-hoc commands
```bash
# Update all Ubuntu containers
ansible ubuntu -m apt -a "update_cache=yes upgrade=dist" --become

# Install a package on specific container
ansible mycontainer -m package -a "name=nginx state=present"

# Run a command on all containers
ansible containers -m shell -a "df -h"
```

### 4. Run playbooks
```bash
# From the lxc environment directory
ansible-playbook ../../playbooks/lxc/setup-webserver.yml

# Target specific groups
ansible-playbook ../../playbooks/lxc/update-containers.yml --limit ubuntu
```

## Container Requirements

For Ansible to work, containers need:
1. Python 3 installed (most images have this)
2. SSH server running (or use `incus exec` connection)
3. The SSH key from `~/.ssh/id_incus.pub` added to authorized_keys

## Creating Ansible-Ready Containers

### For Incus (newer Fedora):
```bash
# Create a basic container
lxcnew mycontainer

# Create with shared directories
lxcnew-shared webdev fedora/40 ~/Projects /home/fedora/Projects
```

### For LXD (older Fedora):
```bash
# Create a basic container
lxc launch images:fedora/39 mycontainer

# Create with shared directories (manual setup required)
lxc launch images:fedora/39 webdev
lxc config device add webdev projects disk source=~/Projects path=/home/fedora/Projects
```

## Custom Container Users

Set custom user in container config:
```bash
# For Incus
lxc config set mycontainer user.ansible_user=myuser

# For LXD
lxc config set mycontainer user.ansible_user=myuser
```

## Setting up Claude Code in Containers

### Quick Setup
Use the provided script for easy setup:
```bash
# Full setup with developer tools
./scripts/setup-claude-in-container.sh mycontainer

# Minimal setup (just Claude and GitHub CLI)
./scripts/setup-claude-in-container.sh mycontainer minimal
```

### Manual Setup with Ansible
```bash
cd environment/lxc

# Full developer setup
ansible-playbook ../../playbooks/lxc/setup-claude-dev.yml --limit mycontainer

# Minimal Claude setup
ansible-playbook ../../playbooks/lxc/setup-claude-minimal.yml --limit mycontainer
```

### What Gets Installed

**Minimal Setup:**
- Node.js 20.12.2 (via NVM)
- Claude Code CLI
- GitHub CLI (gh)

**Full Developer Setup:**
- Everything from minimal plus:
- Development tools: ripgrep, fd, bat, fzf, jq, etc.
- Enhanced shell configuration
- Git aliases and better prompt
- Common development directories

## Troubleshooting

1. **Container not appearing**: Make sure it's running (`lxc list`)
2. **SSH connection failed**: Check if Python is installed in the container
3. **Permission denied**: Ensure the container user has sudo privileges
4. **Claude authentication**: Make sure to copy the full URL when authenticating
5. **Node/npm not found**: Source bashrc after installation: `source ~/.bashrc`