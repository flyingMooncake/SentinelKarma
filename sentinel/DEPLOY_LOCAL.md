# 🚀 Deploy Sentinel Contract to Local Testnet

Complete guide to deploy the fixed Sentinel contract to your local Solana testnet.

---

## 📋 Prerequisites

- [x] Contract bugs fixed (lib_fixed.rs applied)
- [x] Local Solana testnet (solanaTestNetDocker)
- [x] Anchor CLI installed
- [x] Solana CLI installed

---

## 🎯 Deployment Steps

### Step 1: Apply Contract Fixes

If you haven't already:

```bash
cd /home/water/SentinelKarma/sentinel
sudo chown -R water:water /home/water/SentinelKarma/sentinel
cp programs/sentinel/src/lib_fixed.rs programs/sentinel/src/lib.rs
```

### Step 2: Start Local Solana Testnet

```bash
cd /home/water/SentinelKarma/solanaTestNetDocker

# Initialize if first time
./manager.sh --init

# Start validator
./manager.sh --validate
```

**Wait ~30 seconds** for validator to be ready.

### Step 3: Verify Testnet is Running

```bash
# Check validator status
docker exec solana-testnet pgrep -f solana-test-validator

# Test RPC connection
curl -X POST http://localhost:8899 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
```

Expected output: `{"jsonrpc":"2.0","result":"ok","id":1}`

### Step 4: Configure Solana CLI

```bash
# Point to local testnet
solana config set --url http://localhost:8899

# Verify configuration
solana config get
```

Expected output should show:
```
RPC URL: http://localhost:8899
```

### Step 5: Check/Create Wallet

```bash
# Check current wallet
solana address

# If no wallet, create one
solana-keygen new --outfile ~/.config/solana/id.json

# Airdrop SOL for deployment
solana airdrop 10
solana balance
```

### Step 6: Build Contract

```bash
cd /home/water/SentinelKarma/sentinel

# Clean build
anchor clean
anchor build
```

**Verify build succeeded:**
```bash
ls -lh target/deploy/sentinel.so
```

Should show a file ~200-400KB.

### Step 7: Deploy Contract

```bash
cd /home/water/SentinelKarma/sentinel

# Deploy to local testnet
anchor deploy
```

**Expected output:**
```
Deploying cluster: http://localhost:8899
Upgrade authority: <your-pubkey>
Deploying program "sentinel"...
Program path: /home/water/SentinelKarma/sentinel/target/deploy/sentinel.so...
Program Id: Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V

Deploy success
```

### Step 8: Verify Deployment

```bash
# Check program exists
solana program show Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V

# Should show program details
```

---

## 📝 Save RPC Configuration

Create a config file for testing:

```bash
cat > /home/water/SentinelKarma/sentinel/local-testnet.json << 'EOF'
{
  "network": "local",
  "rpcUrl": "http://localhost:8899",
  "wsUrl": "ws://localhost:8900",
  "programId": "Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V",
  "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "endpoints": {
    "rpc": "http://localhost:8899",
    "websocket": "ws://localhost:8900",
    "gossip": "localhost:8001"
  },
  "wallet": "~/.config/solana/id.json"
}
EOF
```

---

## 🧪 Test Deployment

### Quick Test with Solana CLI

```bash
# Get program account info
solana account Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V

# Should show:
# - Balance (rent-exempt amount)
# - Owner: BPFLoaderUpgradeab1e11111111111111111111111
# - Executable: true
```

### Test with Anchor

```bash
cd /home/water/SentinelKarma/sentinel

# Run tests against local testnet
anchor test --skip-local-validator
```

---

## 📊 Deployment Info

After successful deployment, save this info:

| Item | Value |
|------|-------|
| **Network** | Local Testnet |
| **RPC URL** | http://localhost:8899 |
| **WebSocket** | ws://localhost:8900 |
| **Program ID** | Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V |
| **Wallet** | ~/.config/solana/id.json |
| **Cluster** | localnet |

---

## 🔧 Troubleshooting

### Validator Not Running

```bash
cd /home/water/SentinelKarma/solanaTestNetDocker
./manager.sh --status

# If not running, start it
./manager.sh --validate
```

### RPC Connection Failed

```bash
# Check if port 8899 is accessible
curl http://localhost:8899

# Check validator logs
docker exec solana-testnet tail -f /solana/validator.log
```

### Deployment Failed - Insufficient Funds

```bash
# Airdrop more SOL
solana airdrop 10
solana balance

# Try deploy again
anchor deploy
```

### Deployment Failed - Program Already Exists

```bash
# If you need to redeploy, use upgrade
anchor upgrade target/deploy/sentinel.so --program-id Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
```

### Build Failed

```bash
# Make sure fixes are applied
diff programs/sentinel/src/lib.rs programs/sentinel/src/lib_fixed.rs

# If different, apply fix
cp programs/sentinel/src/lib_fixed.rs programs/sentinel/src/lib.rs

# Clean and rebuild
anchor clean
anchor build
```

---

## 🎯 Next Steps After Deployment

1. **Test the contract** - See `TEST_CONTRACT.md`
2. **Initialize the program** - Call `initialize` instruction
3. **Create test accounts** - Join network, mint NFTs, etc.
4. **Integration testing** - Test with your application

---

## 📚 Related Files

- `TEST_CONTRACT.md` - Testing guide (to be created)
- `local-testnet.json` - RPC configuration
- `../solanaTestNetDocker/` - Local testnet manager

---

## ✅ Deployment Checklist

- [ ] Contract fixes applied
- [ ] Local testnet running
- [ ] Solana CLI configured
- [ ] Wallet funded with SOL
- [ ] Contract built successfully
- [ ] Contract deployed successfully
- [ ] Deployment verified
- [ ] RPC config saved
- [ ] Ready for testing

---

**Status**: Ready to deploy! 🚀

Run the commands in order and you'll have your contract deployed to the local testnet.
