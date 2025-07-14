#!/usr/bin/env python3
"""
Dynamic inventory script for Incus/LXD containers
Returns all containers with their IP addresses for Ansible
Supports both Incus and LXD for backwards compatibility
"""

import json
import subprocess
import sys
import os


def detect_container_command():
    """Detect whether to use incus or lxc command"""
    # First try incus (preferred for newer systems)
    try:
        subprocess.run(['incus', 'version'], capture_output=True, check=True)
        return 'incus'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fall back to lxc (LXD)
    try:
        subprocess.run(['lxc', 'version'], capture_output=True, check=True)
        return 'lxc'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return None


def get_containers():
    """Get list of all containers with their details"""
    cmd = detect_container_command()
    if not cmd:
        print("Error: Neither incus nor lxc command found. Please install Incus or LXD.", file=sys.stderr)
        return []

    try:
        # Get container list in JSON format
        result = subprocess.run(
            [cmd, 'list', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout), cmd
    except subprocess.CalledProcessError:
        print(f"Error: Unable to list containers using {cmd}. Is the service running?", file=sys.stderr)
        return [], cmd
    except json.JSONDecodeError:
        print(f"Error: Unable to parse {cmd} output", file=sys.stderr)
        return [], cmd


def get_container_ip(container):
    """Extract the IPv4 address from container state"""
    if container.get('status') != 'Running':
        return None

    # Try to get IP from state
    state = container.get('state', {})
    network = state.get('network', {})

    # Look for the first interface with an IPv4 address (usually eth0)
    for iface_name, iface_data in network.items():
        if iface_name == 'lo':  # Skip loopback
            continue
        addresses = iface_data.get('addresses', [])
        for addr in addresses:
            if addr.get('family') == 'inet' and addr.get('scope') == 'global':
                return addr.get('address')

    return None


def get_container_config_value(container, key):
    """Get a config value from container"""
    config = container.get('config', {})
    return config.get(key)


def build_inventory():
    """Build Ansible inventory from containers"""
    # Determine SSH key path based on what exists
    ssh_key_paths = [
        os.path.expanduser('~/.ssh/id_incus'),  # New Incus setup
        os.path.expanduser('~/.ssh/id_lxc')     # Old LXC setup
    ]
    ssh_key = None
    for key_path in ssh_key_paths:
        if os.path.exists(key_path):
            ssh_key = key_path
            break
    if not ssh_key:
        ssh_key = ssh_key_paths[0]  # Default to id_incus

    inventory = {
        '_meta': {
            'hostvars': {}
        },
        'all': {
            'children': ['containers']
        },
        'containers': {
            'hosts': [],
            'vars': {
                'ansible_user': 'ec',
                'ansible_ssh_private_key_file': ssh_key,
                'ansible_ssh_common_args': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
            }
        },
        # Backwards compatibility aliases
        'incus_containers': {
            'children': ['containers']
        },
        'lxc_containers': {
            'children': ['containers']
        },
        'running': {
            'hosts': []
        },
        'stopped': {
            'hosts': []
        }
    }

    containers, cmd_used = get_containers()

    for container in containers:
        name = container.get('name')
        status = container.get('status', 'Unknown')

        if not name:
            continue

        # Add to main group
        inventory['containers']['hosts'].append(name)

        # Add to status-based groups
        if status == 'Running':
            inventory['running']['hosts'].append(name)
            ip = get_container_ip(container)

            if ip:
                # Add host variables
                inventory['_meta']['hostvars'][name] = {
                    'ansible_host': ip,
                    'container_status': status,
                    'container_type': container.get('type', 'container'),
                    'container_command': cmd_used  # Track which command is being used
                }

                # Check for custom ansible_user in container config
                custom_user = get_container_config_value(container, 'user.ansible_user')
                if custom_user:
                    inventory['_meta']['hostvars'][name]['ansible_user'] = custom_user
        else:
            inventory['stopped']['hosts'].append(name)
            inventory['_meta']['hostvars'][name] = {
                'container_status': status,
                'container_type': container.get('type', 'container'),
                'container_command': cmd_used
            }

        # Add container to image-based groups (e.g., ubuntu, fedora)
        image_info = container.get('config', {}).get('image.description', '')
        if 'ubuntu' in image_info.lower():
            if 'ubuntu' not in inventory:
                inventory['ubuntu'] = {'hosts': []}
            inventory['ubuntu']['hosts'].append(name)
        elif 'fedora' in image_info.lower():
            if 'fedora' not in inventory:
                inventory['fedora'] = {'hosts': []}
            inventory['fedora']['hosts'].append(name)
            # Fedora containers typically use a different default user
            if name in inventory['_meta']['hostvars']:
                inventory['_meta']['hostvars'][name].setdefault('ansible_user', 'fedora')
        elif 'alpine' in image_info.lower():
            if 'alpine' not in inventory:
                inventory['alpine'] = {'hosts': []}
            inventory['alpine']['hosts'].append(name)

    return inventory


def main():
    """Main function"""
    # Check for --list argument (required by Ansible)
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        inventory = build_inventory()
        print(json.dumps(inventory, indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        # Return empty host vars (already provided in _meta)
        print(json.dumps({}))
    else:
        print("Usage: {} --list or {} --host <hostname>".format(sys.argv[0], sys.argv[0]))
        sys.exit(1)


if __name__ == '__main__':
    main()
