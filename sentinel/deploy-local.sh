#!/usr/bin/env bash
set -euo pipefail

# Deploy Sentinel contract to local Solana testnet using key from keymanager
# Usage: ./deploy-local.sh [key_index]

KEY_INDEX="${1:-2}"  # Default to key [2]
SOLANA_TESTNET_DIR="../solanaTestNetDocker"
RPC_URL="http://localhost:8899"

info() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err()  { printf "\033[1;31m[ERR ]\033[0m %s\n" "$*" >&2; }
die()  { err "$*"; exit 1; }

# Check if solana testnet is running
check_testnet() {
    info "Checking if Solana testnet is running..."
    if ! docker ps | grep -q "solana-testnet"; then
        die "Solana testnet container is not running. Start it first with: cd $SOLANA_TESTNET_DIR && ./manager.sh --validate"
    fi
    
    # Check if RPC is responding
    if ! curl -sf "$RPC_URL" -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' >/dev/null 2>&1; then
        die "Solana RPC at $RPC_URL is not responding. Check if validator is running."
    fi
    
    info "✓ Solana testnet is running"
}

# Get keypair from keymanager
get_keypair() {
    info "Getting keypair [${KEY_INDEX}] from keymanager..."
    
    cd "$SOLANA_TESTNET_DIR"
    
    # Get list of keys and extract the one at KEY_INDEX
    local keyfile=$(./keymanager.sh --list 2>/dev/null | grep "^\[${KEY_INDEX}\]" | grep -oP 'Path: \K.*' || true)
    
    if [[ -z "$keyfile" ]]; then
        die "Key [${KEY_INDEX}] not found. Run: cd $SOLANA_TESTNET_DIR && ./keymanager.sh --list"
    fi
    
    if [[ ! -f "$keyfile" ]]; then
        die "Keyfile not found: $keyfile"
    fi
    
    # Get public key
    local pubkey=$(docker exec solana-testnet solana-keygen pubkey "$keyfile" 2>/dev/null || true)
    
    if [[ -z "$pubkey" ]]; then
        die "Failed to read public key from $keyfile"
    fi
    
    info "✓ Using key [${KEY_INDEX}]"
    info "  Path: $keyfile"
    info "  Pubkey: $pubkey"
    
    # Check balance
    local balance=$(docker exec solana-testnet solana balance "$keyfile" --url "$RPC_URL" 2>/dev/null || echo "0 SOL")
    info "  Balance: $balance"
    
    # Parse balance (remove " SOL" suffix)
    local balance_num=$(echo "$balance" | awk '{print $1}')
    
    # Check if balance is sufficient (need at least 10 SOL for deployment)
    if (( $(echo "$balance_num < 10" | bc -l) )); then
        warn "Balance is low. Requesting airdrop..."
        ./keymanager.sh --airdrop -n "$KEY_INDEX" 1000 >/dev/null 2>&1 || warn "Airdrop failed, but continuing..."
        sleep 2
        balance=$(docker exec solana-testnet solana balance "$keyfile" --url "$RPC_URL" 2>/dev/null || echo "0 SOL")
        info "  New balance: $balance"
    fi
    
    cd - >/dev/null
    
    echo "$keyfile"
}

# Copy keypair to sentinel directory
setup_keypair() {
    local keyfile="$1"
    local deploy_keypair="./deploy-keypair.json"
    
    info "Setting up deployment keypair..."
    
    # Copy keypair from testnet to sentinel directory
    cp "$keyfile" "$deploy_keypair"
    chmod 600 "$deploy_keypair"
    
    info "✓ Deployment keypair ready: $deploy_keypair"
    
    echo "$deploy_keypair"
}

# Build the contract
build_contract() {
    info "Building Sentinel contract..."
    
    if ! command -v anchor >/dev/null 2>&1; then
        die "Anchor CLI not found. Install it with: cargo install --git https://github.com/coral-xyz/anchor avm --locked --force"
    fi
    
    anchor build --no-idl
    
    if [[ ! -f "target/deploy/sentinel.so" ]]; then
        die "Build failed: target/deploy/sentinel.so not found"
    fi
    
    info "✓ Contract built successfully"
}

# Deploy the contract
deploy_contract() {
    local deploy_keypair="$1"
    
    info "Deploying Sentinel contract to localhost..."
    info "  RPC: $RPC_URL"
    info "  Deployer: $(solana-keygen pubkey "$deploy_keypair" 2>/dev/null)"
    
    # Set Solana config to use localhost
    solana config set --url "$RPC_URL" >/dev/null 2>&1
    solana config set --keypair "$deploy_keypair" >/dev/null 2>&1
    
    # Deploy using anchor
    anchor deploy --provider.cluster localnet --provider.wallet "$deploy_keypair"
    
    if [[ $? -eq 0 ]]; then
        info "✓ Contract deployed successfully!"
        
        # Get program ID
        local program_id=$(solana-keygen pubkey "target/deploy/sentinel-keypair.json" 2>/dev/null || echo "Unknown")
        info "  Program ID: $program_id"
        
        # Verify deployment
        info "Verifying deployment..."
        local account_info=$(solana account "$program_id" --url "$RPC_URL" 2>/dev/null || echo "")
        
        if [[ -n "$account_info" ]]; then
            info "✓ Deployment verified!"
            echo ""
            echo "$account_info"
        else
            warn "Could not verify deployment"
        fi
    else
        die "Deployment failed"
    fi
}

# Initialize the contract
initialize_contract() {
    local deploy_keypair="$1"
    
    info "Initializing Sentinel contract..."
    
    # Check if there's an initialization script
    if [[ -f "scripts/initialize.ts" ]]; then
        info "Running initialization script..."
        ts-node scripts/initialize.ts --keypair "$deploy_keypair" --url "$RPC_URL"
    else
        warn "No initialization script found. You may need to initialize manually."
        info "You can initialize using the test suite or create a custom script."
    fi
}

# Main execution
main() {
    info "=== Sentinel Contract Deployment ==="
    info "Target: Localhost (Solana TestNet Docker)"
    info "Key Index: [${KEY_INDEX}]"
    echo ""
    
    # Check prerequisites
    check_testnet
    
    # Get keypair from keymanager
    local keyfile=$(get_keypair)
    
    # Setup deployment keypair
    local deploy_keypair=$(setup_keypair "$keyfile")
    
    # Build contract
    build_contract
    
    # Deploy contract
    deploy_contract "$deploy_keypair"
    
    echo ""
    info "=== Deployment Complete ==="
    info "Next steps:"
    info "  1. Initialize the contract (if not done automatically)"
    info "  2. Run tests: anchor test --skip-local-validator"
    info "  3. Interact with the contract using the deployed program ID"
    echo ""
    info "Deployment keypair saved at: $deploy_keypair"
    info "Keep this file safe - it's needed for contract upgrades!"
}

# Run main
main
