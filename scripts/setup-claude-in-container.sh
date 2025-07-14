#!/bin/bash
# Quick script to set up Claude Code in a specific container

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if container name is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide a container name${NC}"
    echo "Usage: $0 <container-name> [minimal|full]"
    echo "  minimal - Just Claude and GitHub CLI"
    echo "  full    - Claude plus developer tools (default)"
    exit 1
fi

CONTAINER_NAME="$1"
SETUP_TYPE="${2:-full}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if we're using incus or lxc
if command -v incus &> /dev/null; then
    LXC_CMD="incus"
elif command -v lxc &> /dev/null; then
    LXC_CMD="lxc"
else
    echo -e "${RED}Error: Neither incus nor lxc command found${NC}"
    exit 1
fi

# Check if container exists and is running
if ! $LXC_CMD list --format=json | jq -r '.[].name' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Container '$CONTAINER_NAME' not found${NC}"
    echo -e "Available containers:"
    $LXC_CMD list
    exit 1
fi

# Check if container is running
STATUS=$($LXC_CMD list --format=json | jq -r ".[] | select(.name==\"$CONTAINER_NAME\") | .status")
if [ "$STATUS" != "Running" ]; then
    echo -e "${YELLOW}Container '$CONTAINER_NAME' is not running. Starting it...${NC}"
    $LXC_CMD start "$CONTAINER_NAME"
    sleep 5
fi

# Choose playbook based on setup type
if [ "$SETUP_TYPE" == "minimal" ]; then
    PLAYBOOK="playbooks/lxc/setup-claude-minimal.yml"
else
    PLAYBOOK="playbooks/lxc/setup-claude-dev.yml"
fi

echo -e "${GREEN}Setting up Claude Code in container '$CONTAINER_NAME' (${SETUP_TYPE} setup)...${NC}"

# Change to lxc environment directory
cd "$PROJECT_ROOT/environment/lxc"

# Run the appropriate playbook
echo -e "${YELLOW}Running Ansible playbook...${NC}"
ansible-playbook "../../${PLAYBOOK}" --limit "$CONTAINER_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Claude Code setup complete!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Enter the container: $LXC_CMD shell $CONTAINER_NAME"
    echo "2. Run: claude"
    echo "3. Follow the authentication link"
    echo "4. Configure GitHub: gh auth login"
else
    echo -e "${RED}✗ Setup failed. Check the error messages above.${NC}"
    exit 1
fi