# 📦 Sentinel Program - Ready to Share

## ✅ Safe to Commit to Git

This repository is **safe to share** with your development partner. All keys are **devnet/testnet only**.

---

## 🔑 What Your Partner Needs

### 1. Program Information
- **Program ID**: `Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V`
- **Network**: Solana Devnet
- **RPC**: `https://api.devnet.solana.com`

### 2. Development Keys (in `DEV_KEYS.md`)
- Devnet wallet keypair
- Program keypair
- Safe to use for testing

### 3. Documentation
- `DEPLOYMENT_INFO.md` - Public deployment details
- `DEV_KEYS.md` - Development keys
- `SECURITY_NOTICE.md` - Security guidelines
- `README.md` - Project overview

---

## 🚀 Quick Start for Your Partner

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd sentinel
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Connect to Devnet
```javascript
import { Connection, PublicKey } from '@solana/web3.js';

const connection = new Connection('https://api.devnet.solana.com', 'confirmed');
const programId = new PublicKey('Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V');
```

### 4. Import Dev Keys (Optional)
If they need to test transactions:
- Open `DEV_KEYS.md`
- Import the wallet to Phantom/Solflare
- Label it "Sentinel Devnet"
- Get devnet SOL: `solana airdrop 2 --url devnet`

---

## 📁 Files to Share

### ✅ Safe to Commit
- `programs/` - Program source code
- `tests/` - Test files
- `target/idl/` - IDL files
- `target/deploy/sentinel-keypair.json` - Devnet program key
- `Anchor.toml` - Configuration
- `Cargo.toml` - Dependencies
- `package.json` - Node dependencies
- `README.md` - Documentation
- `DEPLOYMENT_INFO.md` - Deployment details
- `DEV_KEYS.md` - Development keys
- `SECURITY_NOTICE.md` - Security info

### ❌ Protected by .gitignore
- `mainnet-*.json` - Mainnet keys (future)
- `production-*.json` - Production keys (future)
- `.env.production` - Production config
- `node_modules/` - Dependencies
- `target/` (except IDL and keypair)

---

## 🎯 What Your Partner Can Build

### Frontend Features
1. **Connect Wallet** (Phantom, Solflare)
2. **Initialize Program** (one-time setup)
3. **Join Network** (pay 1000 SentinelCoin)
4. **Mint NFT** (create post with hash + db address)
5. **Like Posts** (increase karma)
6. **View Karma** (display peer karma)
7. **Cycle Info** (show time until next cycle)

### Example UI Flow
```
1. User connects wallet
2. Check if user is a peer
3. If not → Show "Join Network" button (costs 1000 tokens)
4. If yes → Show:
   - Mint NFT form
   - Feed of posts
   - Like buttons
   - Karma leaderboard
   - Cycle countdown
```

---

## 🔗 Important Links

**Explorer**:
https://explorer.solana.com/address/Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V?cluster=devnet

**Devnet Faucet**:
https://faucet.solana.com/

**Solana Docs**:
https://docs.solana.com/

**Anchor Docs**:
https://www.anchor-lang.com/

---

## ⚠️ Important Reminders

### For Development
✅ Use devnet keys freely  
✅ Test all features  
✅ Share keys with team  
✅ No real funds at risk  

### For Production (Later)
❌ NEVER use devnet keys on mainnet  
✅ Generate new keypairs  
✅ Use hardware wallet  
✅ Set up proper security  

---

## 📞 Communication

### Share This Repository
```bash
# Push to GitHub/GitLab
git add .
git commit -m "Add Sentinel program with devnet deployment"
git push origin main
```

### Tell Your Partner
"I've deployed the Sentinel program to Solana devnet. The repo includes:
- Program source code
- Devnet deployment (Program ID: Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V)
- Development keys (safe to use for testing)
- Full documentation

Check `DEPLOYMENT_INFO.md` for connection details and `DEV_KEYS.md` for test keys. Everything is ready for web integration!"

---

## ✅ Checklist

Before sharing:
- [x] Program deployed to devnet
- [x] Documentation complete
- [x] Dev keys documented
- [x] .gitignore configured
- [x] Security notice added
- [x] Ready to commit to git

**Status**: 🟢 Ready to Share!
