#!/usr/bin/env bash
set -euo pipefail

# Quick deploy - handles everything automatically
RPC_URL="http://localhost:8899"

info() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
err()  { printf "\033[1;31m[ERR ]\033[0m %s\n" "$*" >&2; }

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Quick Sentinel Deployment to Localhost           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if testnet is running
if ! docker ps | grep -q "solana-testnet"; then
    err "Solana testnet not running. Starting it..."
    cd solanaTestNetDocker
    
    # Init if needed
    if [ ! -d "data/ledger" ]; then
        info "Initializing testnet..."
        ./manager.sh --init
    fi
    
    info "Starting validator..."
    ./manager.sh --validate
    
    info "Waiting for RPC to be ready..."
    sleep 5
    cd ..
fi

# Wait for RPC
info "Checking RPC..."
for i in {1..30}; do
    if curl -sf "$RPC_URL" -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' >/dev/null 2>&1; then
        info "✓ RPC is ready"
        break
    fi
    [ $i -eq 30 ] && { err "RPC timeout"; exit 1; }
    sleep 1
done

# Generate a deployment key if none exists
DEPLOY_KEY="./sentinel/deploy-keypair.json"
if [ ! -f "$DEPLOY_KEY" ]; then
    info "Generating deployment keypair..."
    solana-keygen new --no-bip39-passphrase --outfile "$DEPLOY_KEY" --force
fi

PUBKEY=$(solana-keygen pubkey "$DEPLOY_KEY")
info "Deployer: $PUBKEY"

# Configure Solana CLI
solana config set --url "$RPC_URL" >/dev/null 2>&1
solana config set --keypair "$DEPLOY_KEY" >/dev/null 2>&1

# Check balance and airdrop
BALANCE=$(solana balance "$DEPLOY_KEY" --url "$RPC_URL" 2>/dev/null | awk '{print $1}')
info "Balance: $BALANCE SOL"

if (( $(echo "$BALANCE < 10" | bc -l 2>/dev/null || echo "1") )); then
    info "Requesting airdrop..."
    solana airdrop 1000 "$DEPLOY_KEY" --url "$RPC_URL" >/dev/null 2>&1 || true
    sleep 2
fi

# Build
info "Building contract..."
cd sentinel
anchor build --no-idl

# Deploy
info "Deploying..."
anchor deploy --provider.cluster localnet --provider.wallet "$DEPLOY_KEY"

PROGRAM_ID=$(solana-keygen pubkey "target/deploy/sentinel-keypair.json")

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT SUCCESS                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Program ID: $PROGRAM_ID"
echo "Deployer:   $PUBKEY"
echo "RPC:        $RPC_URL"
echo ""
