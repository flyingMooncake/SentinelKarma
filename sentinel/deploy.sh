#!/bin/bash
# Automated deployment script for Sentinel contract to local testnet

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TESTNET_DIR="$ROOT_DIR/solanaTestNetDocker"
PROGRAM_ID="7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7"
RPC_URL="http://localhost:8899"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

die() {
    error "$1"
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "🚀 Sentinel Contract Deployment Script"
echo "========================================"
echo ""

# Step 1: Check prerequisites
info "Checking prerequisites..."

if ! command_exists anchor; then
    die "Anchor CLI not found. Install it first: https://www.anchor-lang.com/docs/installation"
fi

if ! command_exists solana; then
    die "Solana CLI not found. Install it first: https://docs.solana.com/cli/install-solana-cli-tools"
fi

if ! command_exists docker; then
    die "Docker not found. Install it first or run: cd $TESTNET_DIR && ./manager.sh --install"
fi

success "All prerequisites installed"
echo ""

# Step 2: Apply contract fixes
info "Checking if contract fixes are applied..."

if [ ! -f "$SCRIPT_DIR/programs/sentinel/src/lib_fixed.rs" ]; then
    die "lib_fixed.rs not found! Run APPLY_FIX.sh first."
fi

# Check if lib.rs has the fixes (check for 'reset_karma' function)
if ! grep -q "pub fn reset_karma" "$SCRIPT_DIR/programs/sentinel/src/lib.rs"; then
    warn "Contract fixes not applied. Applying now..."
    
    # Fix permissions
    sudo chown -R $USER:$USER "$SCRIPT_DIR" 2>/dev/null || true
    
    # Backup original
    if [ ! -f "$SCRIPT_DIR/programs/sentinel/src/lib.rs.backup" ]; then
        cp "$SCRIPT_DIR/programs/sentinel/src/lib.rs" "$SCRIPT_DIR/programs/sentinel/src/lib.rs.backup"
        info "Original backed up to lib.rs.backup"
    fi
    
    # Apply fix
    cp "$SCRIPT_DIR/programs/sentinel/src/lib_fixed.rs" "$SCRIPT_DIR/programs/sentinel/src/lib.rs"
    success "Contract fixes applied"
else
    success "Contract fixes already applied"
fi
echo ""

# Step 3: Check/Start local testnet
info "Checking local Solana testnet..."

if ! docker ps | grep -q solana-testnet; then
    warn "Local testnet not running. Starting it..."
    
    cd "$TESTNET_DIR"
    
    # Initialize if needed
    if [ ! -d "$TESTNET_DIR/data/config" ]; then
        info "Initializing testnet for first time..."
        ./manager.sh --init
    fi
    
    # Start validator
    info "Starting validator..."
    ./manager.sh --validate
    
    # Wait for validator to be ready
    info "Waiting for validator to be ready..."
    sleep 10
    
    cd "$SCRIPT_DIR"
else
    success "Local testnet is running"
fi
echo ""

# Step 4: Verify testnet is accessible
info "Verifying testnet connection..."

MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -X POST $RPC_URL \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' | grep -q "ok"; then
        success "Testnet is accessible at $RPC_URL"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        die "Testnet not responding after $MAX_RETRIES attempts"
    fi
    
    warn "Waiting for testnet... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done
echo ""

# Step 5: Configure Solana CLI
info "Configuring Solana CLI..."

solana config set --url $RPC_URL > /dev/null
solana config set --keypair ~/.config/solana/id.json > /dev/null
success "Solana CLI configured to use $RPC_URL"
echo ""

# Step 6: Check wallet
info "Checking wallet..."

# Create .config/solana directory if it doesn't exist
mkdir -p ~/.config/solana

if [ ! -f ~/.config/solana/id.json ]; then
    warn "No wallet found. Creating one..."
    solana-keygen new --outfile ~/.config/solana/id.json --no-bip39-passphrase --force
    success "New wallet created"
fi

WALLET_ADDRESS=$(solana address)
success "Wallet address: $WALLET_ADDRESS"
echo ""

# Step 7: Fund wallet
info "Checking wallet balance..."

BALANCE=$(solana balance | awk '{print $1}')
if (( $(echo "$BALANCE < 5" | bc -l) )); then
    warn "Low balance ($BALANCE SOL). Requesting airdrop..."
    solana airdrop 10
    sleep 2
    BALANCE=$(solana balance | awk '{print $1}')
fi

success "Wallet balance: $BALANCE SOL"
echo ""

# Step 8: Build contract
info "Building contract..."

cd "$SCRIPT_DIR"
anchor clean > /dev/null 2>&1 || true
anchor build --no-idl

if [ ! -f "target/deploy/sentinel.so" ]; then
    die "Build failed! Binary not found."
fi

BINARY_SIZE=$(ls -lh target/deploy/sentinel.so | awk '{print $5}')
success "Contract built successfully (size: $BINARY_SIZE)"
echo ""

# Step 9: Deploy contract
info "Deploying contract to local testnet..."

# Check if program already exists
if solana program show $PROGRAM_ID > /dev/null 2>&1; then
    warn "Program already deployed. Upgrading..."
    anchor upgrade target/deploy/sentinel.so --program-id $PROGRAM_ID
else
    info "Deploying new program..."
    anchor deploy
fi

success "Contract deployed successfully!"
echo ""

# Step 10: Verify deployment
info "Verifying deployment..."

if solana program show $PROGRAM_ID > /dev/null 2>&1; then
    success "Program verified on-chain"
    
    # Get program info
    PROGRAM_INFO=$(solana program show $PROGRAM_ID)
    echo ""
    echo "Program Information:"
    echo "==================="
    echo "$PROGRAM_INFO"
else
    die "Deployment verification failed"
fi
echo ""

# Step 11: Save deployment info
info "Saving deployment configuration..."

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

cat > "$SCRIPT_DIR/deployment-info.json" << EOF
{
  "network": "local",
  "rpcUrl": "$RPC_URL",
  "wsUrl": "ws://localhost:8900",
  "programId": "$PROGRAM_ID",
  "deployedAt": "$TIMESTAMP",
  "deployedBy": "$WALLET_ADDRESS",
  "endpoints": {
    "rpc": "$RPC_URL",
    "websocket": "ws://localhost:8900",
    "gossip": "localhost:8001"
  },
  "wallet": "~/.config/solana/id.json",
  "binarySize": "$BINARY_SIZE"
}
EOF

success "Deployment info saved to deployment-info.json"
echo ""

# Step 12: Summary
echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "📊 Deployment Summary:"
echo "  Network:     Local Testnet"
echo "  RPC URL:     $RPC_URL"
echo "  Program ID:  $PROGRAM_ID"
echo "  Wallet:      $WALLET_ADDRESS"
echo "  Balance:     $BALANCE SOL"
echo "  Binary Size: $BINARY_SIZE"
echo ""
echo "🎯 Next Steps:"
echo "  1. Test the contract: anchor test --skip-local-validator"
echo "  2. Initialize program: See TEST_CONTRACT.md"
echo "  3. Create test accounts: Join network, mint NFTs, etc."
echo ""
echo "📚 Useful Commands:"
echo "  Check program:  solana program show $PROGRAM_ID"
echo "  View logs:      docker exec solana-testnet tail -f /solana/validator.log"
echo "  Stop testnet:   cd $TESTNET_DIR && ./manager.sh --stops"
echo ""
echo "🎉 Happy testing!"
