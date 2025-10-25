#!/bin/bash
# Fix Node.js installation conflict

echo "Fixing Node.js installation conflict..."

# Remove conflicting packages
echo "Removing old Node.js packages..."
sudo apt-get remove -y libnode-dev node-gyp libnode72 nodejs-doc 2>/dev/null || true
sudo apt-get remove -y nodejs npm 2>/dev/null || true

# Clean up
echo "Cleaning up..."
sudo apt-get autoremove -y
sudo apt-get clean
sudo rm -rf /var/cache/apt/archives/nodejs*.deb

# Setup Node.js 20 repository
echo "Setting up Node.js 20 repository..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Force install with overwrite
echo "Installing Node.js 20..."
sudo dpkg -i --force-overwrite /var/cache/apt/archives/nodejs*.deb 2>/dev/null || true
sudo apt-get install -f -y
sudo apt-get install -y nodejs

# Verify installation
echo ""
echo "Verification:"
echo "Node.js version: $(node --version 2>/dev/null || echo 'Not installed')"
echo "npm version: $(npm --version 2>/dev/null || echo 'Not installed')"

echo ""
echo "✅ Fix complete! You can now run: ./manager.sh --install"