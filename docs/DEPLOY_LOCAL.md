# Deploy Sentinel Contract to Local Testnet

This guide shows how to deploy the Sentinel smart contract to your local Solana testnet using a key from the keymanager.

## Prerequisites

1. **Solana testnet running** (from solanaTestNetDocker submodule)
2. **Anchor CLI installed** (`cargo install --git https://github.com/coral-xyz/anchor avm --locked --force`)
3. **Node.js and npm** (for Anchor)
4. **Rust toolchain** (for building the contract)

## Quick Start

### 1. Start the Solana Testnet

```bash
cd solanaTestNetDocker
./manager.sh --init      # First time only
./manager.sh --validate  # Start the validator
```

Verify it's running:
```bash
curl http://localhost:8899 -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
```

### 2. Check Available Keys

```bash
cd solanaTestNetDocker
./keymanager.sh --list
```

You should see output like:
```
[INFO] Available Keys:

[1] validator-keypair.json
    Path: ./data/config/validator-keypair.json
    Public Key: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU

[2] vote-account-keypair.json
    Path: ./data/config/vote-account-keypair.json
    Public Key: AnotherPublicKeyHere...

[3] wallet-20250115-123456.json
    Path: ./data/accounts/wallet-20250115-123456.json
    Public Key: YetAnotherPublicKeyHere...
```

### 3. Ensure Key Has Balance

Check balance of key [2]:
```bash
cd solanaTestNetDocker
./keymanager.sh --balance -n 2
```

If balance is low, airdrop some SOL:
```bash
./keymanager.sh --airdrop -n 2 1000
```

### 4. Deploy the Contract

From the project root:
```bash
./deploy-sentinel-local.sh 2
```

This will:
- ✓ Check if Solana testnet is running
- ✓ Get keypair [2] from keymanager
- ✓ Ensure sufficient balance (auto-airdrop if needed)
- ✓ Build the Sentinel contract
- ✓ Deploy to localhost
- ✓ Verify deployment

### 5. Verify Deployment

After successful deployment, you'll see:
```
╔════════════════════════════════════════════════════════════╗
║                  DEPLOYMENT SUCCESSFUL                     ║
╚════════════════════════════════════════════════════════════╝

Program ID: Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
Deployer:   YourPublicKeyHere...
Network:    Localhost (http://localhost:8899)
```

Check the program account:
```bash
solana account Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V --url http://localhost:8899
```

## Using Different Keys

Deploy with a different key (e.g., key [3]):
```bash
./deploy-sentinel-local.sh 3
```

## Initialize the Contract

After deployment, initialize the contract:

### Option 1: Using Anchor Tests
```bash
cd sentinel
anchor test --skip-local-validator
```

### Option 2: Using Custom Script
Create `sentinel/scripts/initialize.ts`:
```typescript
import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Sentinel } from "../target/types/sentinel";

async function main() {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);
  
  const program = anchor.workspace.Sentinel as Program<Sentinel>;
  
  // Initialize the contract
  const tx = await program.methods.initialize()
    .accounts({
      authority: provider.wallet.publicKey,
      // ... other accounts
    })
    .rpc();
  
  console.log("Initialized! Transaction:", tx);
}

main().catch(console.error);
```

Run it:
```bash
cd sentinel
ts-node scripts/initialize.ts
```

## Troubleshooting

### Testnet Not Running
```
[ERR ] Solana testnet is not running!

Start it with:
  cd solanaTestNetDocker
  ./manager.sh --init
  ./manager.sh --validate
```

### Key Not Found
```
[ERR ] Key [2] not found!

Available keys:
[1] validator-keypair.json
...
```

Solution: Use a valid key index or generate a new one:
```bash
cd solanaTestNetDocker
./keymanager.sh --generate my-deployer
./keymanager.sh --airdrop -n 3 1000  # If it's the 3rd key
```

### Insufficient Balance
The script will automatically airdrop 1000 SOL if balance is below 10 SOL.

Manual airdrop:
```bash
cd solanaTestNetDocker
./keymanager.sh --airdrop -n 2 1000
```

### Anchor Not Found
```
[ERR ] Anchor CLI not found. Install it first.
```

Install Anchor:
```bash
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install latest
avm use latest
```

### Build Fails
```
[ERR ] Build failed: target/deploy/sentinel.so not found
```

Check Rust toolchain:
```bash
rustc --version
cargo --version
```

Install/update Rust:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Deployment Fails
Check deployer balance:
```bash
cd solanaTestNetDocker
./keymanager.sh --balance -n 2
```

Check validator logs:
```bash
docker exec solana-testnet tail -f /solana/validator.log
```

## Files Created

After deployment:
- `sentinel/deploy-keypair.json` - Deployment keypair (keep safe!)
- `sentinel/target/deploy/sentinel.so` - Compiled program
- `sentinel/target/deploy/sentinel-keypair.json` - Program keypair

## Network Configuration

The deployment uses:
- **RPC URL**: http://localhost:8899
- **WebSocket**: ws://localhost:8900
- **Cluster**: Localnet
- **Commitment**: Confirmed

## Next Steps

1. **Initialize the contract** with your authority key
2. **Run tests** to verify functionality
3. **Interact with the contract** using Anchor or web3.js
4. **Monitor transactions** on the local explorer

## Advanced: Multiple Deployments

To deploy multiple instances:

1. Generate new program keypair:
```bash
cd sentinel
solana-keygen new -o target/deploy/sentinel-v2-keypair.json
```

2. Update `Anchor.toml`:
```toml
[programs.localnet]
sentinel = "NewProgramIDHere"
```

3. Deploy:
```bash
anchor deploy --program-name sentinel --program-keypair target/deploy/sentinel-v2-keypair.json
```

## Useful Commands

```bash
# Check Solana config
solana config get

# Check program account
solana account <PROGRAM_ID> --url http://localhost:8899

# Get program logs
solana logs <PROGRAM_ID> --url http://localhost:8899

# Check transaction
solana confirm <SIGNATURE> --url http://localhost:8899

# List all programs
solana program show --programs --url http://localhost:8899
```

## Security Notes

⚠️ **Important**: The deployment keypair (`deploy-keypair.json`) has upgrade authority over the program. Keep it secure!

For production:
- Use a hardware wallet or multisig for deployment
- Transfer upgrade authority to a secure multisig
- Consider making the program immutable after testing
