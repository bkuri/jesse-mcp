#!/bin/bash
# push-deploy.sh - Push to origin and deploy to server2 via git pull
# Usage: ./scripts/push-deploy.sh [git-push-args...]

set -e

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Only deploy from main or master branch
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo "Not on main/master branch (currently on $BRANCH), skipping deployment"
    git push "$@"
    exit 0
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Uncommitted changes detected, please commit first"
    exit 1
fi

# Push to remote
echo "Pushing to origin..."
git push "$@"

# Check if push succeeded
if [ $? -eq 0 ]; then
    echo "Push successful"
    echo ""
    echo "Deploying to server2..."
    
    # Deploy to server2
    ssh server2-auto << 'ENDSSH'
set -e
cd /srv/containers/jesse-mcp
echo "  Pulling latest changes..."
git pull
echo "  Reinstalling package..."
/srv/containers/jesse-mcp/.venv/bin/python -m pip install -e .
echo "  Restarting mcproxy service..."
sudo systemctl restart mcproxy
sleep 2
echo "  Checking service status..."
if sudo systemctl is-active --quiet mcproxy; then
    echo "  mcproxy is running"
else
    echo "  mcproxy failed to start"
    sudo systemctl status mcproxy --no-pager
    exit 1
fi
ENDSSH
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "Deployment complete!"
    else
        echo ""
        echo "Deployment failed"
        exit 1
    fi
else
    echo "Push failed, skipping deployment"
    exit 1
fi
