# 🔑 Development Keys (Devnet Only)

## ⚠️ IMPORTANT: These are DEVELOPMENT keys for DEVNET ONLY

**These keys are safe to share with your development team.**  
**They will NOT be used for mainnet/production.**  
**No real funds are at risk.**

---

## 1️⃣ Development Wallet (Deployer/Authority)

### Public Key (Address)
Get with: `solana address`

### Private Key (Byte Array)
**Location**: `~/.config/solana/id.json`

```json
[122,32,178,110,110,158,62,31,165,41,32,203,54,15,176,242,141,248,136,2,45,237,216,98,255,247,224,169,91,79,232,31,149,253,136,210,150,192,146,62,47,135,198,149,206,54,19,41,48,177]
```

### Usage
- Deploy programs to devnet
- Initialize the Sentinel program
- Authority for program operations
- Testing transactions

---

## 2️⃣ Program Keypair (Devnet)

### Program ID (Public)
```
Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
```

### Private Key (Byte Array)
**Location**: `target/deploy/sentinel-keypair.json`

```json
[43,238,58,183,217,31,215,44,93,42,117,61,47,228,216,170,121,102,227,252,86,125,195,72,4,196,102,51,121,84,92,63,77,39,46,111,87,85,238,29,196,244,30,85,205,162,161,156,0,150,191,241,246]
```

### Usage
- Upgrade authority for the devnet program
- Deploy program updates
- Testing program upgrades

---

## 📱 Import to Wallet (For Testing)

### Phantom Wallet
1. Open Phantom
2. Settings → Add/Import Account
3. Import Private Key
4. Paste the byte array above
5. **Label it "Sentinel Devnet"** so you don't confuse it with mainnet

### Solflare
1. Open Solflare
2. Add Account → Import Private Key
3. Paste the private key
4. Label as "Devnet Testing"

### JavaScript/TypeScript
```javascript
import { Keypair } from '@solana/web3.js';

// Development wallet
const devWallet = Keypair.fromSecretKey(
  Uint8Array.from([122,32,178,110,110,158,62,31,165,41,32,203,54,15,176,242,141,248,136,2,45,237,216,98,255,247,224,169,91,79,232,31,149,253,136,210,150,192,146,62,47,135,198,149,206,54,19,41,48,177])
);

// Program keypair
const programKeypair = Keypair.fromSecretKey(
  Uint8Array.from([43,238,58,183,217,31,215,44,93,42,117,61,47,228,216,170,121,102,227,252,86,125,195,72,4,196,102,51,121,84,92,63,77,39,46,111,87,85,238,29,196,244,30,85,205,162,161,156,0,150,191,241,246])
);

console.log('Dev Wallet:', devWallet.publicKey.toString());
console.log('Program ID:', programKeypair.publicKey.toString());
```

---

## 🔄 For Production/Mainnet

### ⚠️ NEVER use these keys on mainnet!

When deploying to mainnet, you will:

1. **Generate NEW keypairs**
   ```bash
   # New wallet for mainnet
   solana-keygen new -o mainnet-wallet.json
   
   # New program keypair for mainnet
   solana-keygen new -o mainnet-program-keypair.json
   ```

2. **Deploy with new keys**
   ```bash
   solana config set --url mainnet-beta
   solana program deploy target/deploy/sentinel.so \
     --program-id mainnet-program-keypair.json \
     --keypair mainnet-wallet.json
   ```

3. **Secure mainnet keys properly**
   - Use hardware wallet (Ledger)
   - Use multisig for program authority
   - Store in secure vault (not in git)
   - Use environment variables

---

## 🧪 Development Workflow

### 1. Your Partner Can:
✅ Import these keys for testing  
✅ Deploy test transactions  
✅ Test the web interface  
✅ Debug program interactions  
✅ Share these keys with other devs  

### 2. For Mainnet Launch:
❌ Do NOT use these keys  
✅ Generate fresh keypairs  
✅ Use hardware wallet  
✅ Set up proper key management  
✅ Use multisig for program authority  

---

## 💰 Get Devnet SOL

```bash
# Using CLI
solana airdrop 2 --url devnet

# Or use faucet
https://faucet.solana.com/
```

---

## 🔐 Key Management Strategy

### Development (Current)
- Keys in git: ✅ OK (devnet only)
- Shared with team: ✅ OK
- Used for testing: ✅ OK
- Risk: ⚠️ None (testnet tokens have no value)

### Production (Future)
- Keys in git: ❌ NEVER
- Shared with team: ❌ Only via secure channels
- Used for testing: ❌ Use devnet keys
- Risk: 🔴 HIGH (real funds)

---

## 📋 Checklist for Mainnet

Before deploying to mainnet:

- [ ] Generate new wallet keypair
- [ ] Generate new program keypair
- [ ] Fund new wallet with real SOL
- [ ] Test deployment on devnet first
- [ ] Set up hardware wallet
- [ ] Configure multisig (optional but recommended)
- [ ] Update program authority
- [ ] Secure backup of keys
- [ ] Document key locations (securely)
- [ ] Set up monitoring

---

## 🆘 If Devnet Keys Are Compromised

**Don't worry!** These are devnet keys:
- No real funds at risk
- Just generate new ones
- Redeploy to devnet
- Update your team

```bash
# Generate new devnet keys
solana-keygen new -o ~/.config/solana/devnet-id.json --force
solana-keygen new -o target/deploy/sentinel-keypair.json --force

# Redeploy
solana config set --url devnet
anchor build --no-idl
solana program deploy target/deploy/sentinel.so \
  --program-id target/deploy/sentinel-keypair.json
```

---

## 📝 Summary

✅ **Safe to commit to git** (devnet only)  
✅ **Safe to share with dev team**  
✅ **Use for development and testing**  
❌ **NEVER use on mainnet**  
❌ **Generate new keys for production**  

**These keys are for development purposes only!**
