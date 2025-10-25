#!/usr/bin/env bash
set -euo pipefail

# Deploy Sentinel contract to local Solana testnet
# Usage: ./deploy-sentinel-local.sh [key_index]

KEY_INDEX="${1:-2}"  # Default to key [2]
SOLANA_DIR="./solanaTestNetDocker"
SENTINEL_DIR="./sentinel"
RPC_URL="http://localhost:8899"

info() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err()  { printf "\033[1;31m[ERR ]\033[0m %s\n" "$*" >&2; }
die()  { err "$*"; exit 1; }

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Sentinel Contract Deployment to Local Testnet         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check if Solana testnet is running
info "Step 1: Checking Solana testnet..."
if ! docker ps | grep -q "solana-testnet"; then
    err "Solana testnet is not running!"
    echo ""
    echo "Start it with:"
    echo "  cd $SOLANA_DIR"
    echo "  ./manager.sh --init"
    echo "  ./manager.sh --validate"
    exit 1
fi

if ! curl -sf "$RPC_URL" -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' >/dev/null 2>&1; then
    die "Solana RPC at $RPC_URL is not responding"
fi
info "✓ Solana testnet is running"
echo ""

# Step 2: Get keypair from keymanager
info "Step 2: Getting keypair [${KEY_INDEX}] from keymanager..."
cd "$SOLANA_DIR"

# List keys and find the one we want
KEYFILE=$(./keymanager.sh --list 2>/dev/null | grep "^\[${KEY_INDEX}\]" -A 1 | grep "Path:" | awk '{print $2}')

if [[ -z "$KEYFILE" ]]; then
    err "Key [${KEY_INDEX}] not found!"
    echo ""
    echo "Available keys:"
    ./keymanager.sh --list
    exit 1
fi

if [[ ! -f "$KEYFILE" ]]; then
    die "Keyfile not found: $KEYFILE"
fi

PUBKEY=$(docker exec solana-testnet solana-keygen pubkey "$KEYFILE" 2>/dev/null)
BALANCE=$(docker exec solana-testnet solana balance "$KEYFILE" --url "$RPC_URL" 2>/dev/null)

info "✓ Using key [${KEY_INDEX}]"
echo "  Path: $KEYFILE"
echo "  Pubkey: $PUBKEY"
echo "  Balance: $BALANCE"
echo ""

# Check if balance is sufficient
BALANCE_NUM=$(echo "$BALANCE" | awk '{print $1}')
if (( $(echo "$BALANCE_NUM < 10" | bc -l 2>/dev/null || echo "1") )); then
    warn "Balance is low. Requesting airdrop of 1000 SOL..."
    ./keymanager.sh --airdrop -n "$KEY_INDEX" 1000 2>&1 | grep -E "(successful|Balance)" || true
    sleep 2
    BALANCE=$(docker exec solana-testnet solana balance "$KEYFILE" --url "$RPC_URL" 2>/dev/null)
    info "  New balance: $BALANCE"
    echo ""
fi

cd - >/dev/null

# Step 3: Copy keypair to sentinel directory
info "Step 3: Setting up deployment keypair..."
DEPLOY_KEYPAIR="$SENTINEL_DIR/deploy-keypair.json"
cp "$KEYFILE" "$DEPLOY_KEYPAIR"
chmod 600 "$DEPLOY_KEYPAIR"
info "✓ Deployment keypair ready"
echo ""

# Step 4: Configure Solana CLI
info "Step 4: Configuring Solana CLI..."
solana config set --url "$RPC_URL" >/dev/null 2>&1
solana config set --keypair "$DEPLOY_KEYPAIR" >/dev/null 2>&1
info "✓ Solana CLI configured for localhost"
echo ""

# Step 5: Build the contract
info "Step 5: Building Sentinel contract..."
cd "$SENTINEL_DIR"

if ! command -v anchor >/dev/null 2>&1; then
    die "Anchor CLI not found. Install it first."
fi

anchor build --no-idl

if [[ ! -f "target/deploy/sentinel.so" ]]; then
    die "Build failed: target/deploy/sentinel.so not found"
fi

PROGRAM_SIZE=$(du -h target/deploy/sentinel.so | awk '{print $1}')
info "✓ Contract built successfully (size: $PROGRAM_SIZE)"
echo ""

# Step 6: Deploy the contract
info "Step 6: Deploying contract to localhost..."
echo "  RPC: $RPC_URL"
echo "  Deployer: $PUBKEY"
echo ""

# Deploy using anchor
if anchor deploy --provider.cluster localnet --provider.wallet "$DEPLOY_KEYPAIR"; then
    info "✓ Contract deployed successfully!"
    echo ""
    
    # Get program ID
    PROGRAM_ID=$(solana-keygen pubkey "target/deploy/sentinel-keypair.json" 2>/dev/null)
    
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                  DEPLOYMENT SUCCESSFUL                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Program ID: $PROGRAM_ID"
    echo "Deployer:   $PUBKEY"
    echo "Network:    Localhost ($RPC_URL)"
    echo ""
    
    # Verify deployment
    info "Verifying deployment..."
    if solana account "$PROGRAM_ID" --url "$RPC_URL" >/dev/null 2>&1; then
        info "✓ Program account exists on-chain"
        
        # Show account info
        echo ""
        solana account "$PROGRAM_ID" --url "$RPC_URL" | head -10
    else
        warn "Could not verify program account"
    fi
    
    echo ""
    info "Next steps:"
    echo "  1. Initialize the contract (run initialization script or tests)"
    echo "  2. Test: cd sentinel && anchor test --skip-local-validator"
    echo "  3. Update Anchor.toml with the new program ID if needed"
    echo ""
    info "Deployment keypair saved at: $DEPLOY_KEYPAIR"
    warn "Keep this file safe - it's needed for contract upgrades!"
    
else
    die "Deployment failed!"
fi

cd - >/dev/null
