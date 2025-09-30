# 🔒 Security Notice

## Development vs Production Keys

### ✅ What's in This Repository (Safe)

This repository contains **DEVNET/TESTNET keys only**:

- `target/deploy/sentinel-keypair.json` - Devnet program keypair
- Development wallet keys documented in `DEV_KEYS.md`
- Program ID: `Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V` (Devnet)

**These keys are safe to share with your development team.**

### ⚠️ Why This Is Safe

1. **Devnet tokens have NO real value**
2. **These keys will NEVER be used on mainnet**
3. **Fresh keys will be generated for production**
4. **No real funds are at risk**

### ❌ What's NOT in This Repository (Protected)

The `.gitignore` file protects:

- `mainnet-*.json` - Any mainnet keypairs
- `production-*.json` - Any production keypairs
- `.env.production` - Production environment variables
- `.env.mainnet` - Mainnet configuration

---

## 🚀 For Mainnet Deployment

### Step 1: Generate New Keys

```bash
# DO NOT use devnet keys!
# Generate fresh keypairs for mainnet

# New wallet
solana-keygen new -o mainnet-wallet.json

# New program keypair
solana-keygen new -o mainnet-program-keypair.json
```

### Step 2: Secure the Keys

- ✅ Use hardware wallet (Ledger, Trezor)
- ✅ Store in secure vault (1Password, Bitwarden)
- ✅ Use multisig for program authority
- ✅ Keep offline backups
- ❌ NEVER commit to git
- ❌ NEVER share in plain text

### Step 3: Deploy to Mainnet

```bash
solana config set --url mainnet-beta

# Deploy with NEW keys
solana program deploy target/deploy/sentinel.so \
  --program-id mainnet-program-keypair.json \
  --keypair mainnet-wallet.json
```

---

## 👥 For Your Development Partner

### What They Can Do

✅ Clone this repository  
✅ Use the devnet keys for testing  
✅ Import keys to Phantom/Solflare (label as "Devnet")  
✅ Build and test the web interface  
✅ Deploy test transactions  
✅ Share devnet keys with other developers  

### What They Should NOT Do

❌ Use these keys on mainnet  
❌ Send real SOL to these addresses  
❌ Assume these keys are production-ready  
❌ Store real user funds with these keys  

---

## 📋 Key Management Checklist

### Development Phase (Current)
- [x] Devnet keys generated
- [x] Program deployed to devnet
- [x] Keys documented for team
- [x] `.gitignore` configured
- [x] Team can test freely

### Pre-Mainnet Phase (Before Launch)
- [ ] Generate new mainnet wallet
- [ ] Generate new program keypair
- [ ] Set up hardware wallet
- [ ] Configure multisig (recommended)
- [ ] Test on devnet with new keys
- [ ] Secure backup of mainnet keys
- [ ] Document key locations (securely)
- [ ] Set up monitoring and alerts

### Mainnet Phase (Production)
- [ ] Deploy with mainnet keys
- [ ] Verify program on explorer
- [ ] Transfer upgrade authority to multisig
- [ ] Set up key rotation policy
- [ ] Monitor program activity
- [ ] Regular security audits

---

## 🔐 Best Practices

### For Development
```bash
# Always specify devnet
solana config set --url devnet

# Label wallets clearly
# In Phantom: "Sentinel Devnet - DO NOT USE ON MAINNET"
```

### For Production
```bash
# Use hardware wallet
solana config set --keypair usb://ledger

# Or use multisig
# Set up with Squads Protocol or similar
```

---

## 🆘 Emergency Procedures

### If Devnet Keys Are Compromised
**Impact**: Low (no real funds)

1. Generate new devnet keys
2. Redeploy to devnet
3. Update team with new keys
4. Continue development

### If Mainnet Keys Are Compromised
**Impact**: HIGH (real funds at risk!)

1. **IMMEDIATELY** transfer all funds to secure wallet
2. Deploy new program with new keys
3. Notify all users
4. Migrate to new program
5. Conduct security audit
6. Review access controls

---

## 📞 Questions?

If you're unsure about key management:

1. **For Development**: Use the devnet keys freely
2. **For Production**: Consult with security expert
3. **For Mainnet**: Use hardware wallet + multisig

---

## ✅ Summary

**Current Status**: 🟢 Safe for Development

- Devnet keys in repository: ✅ OK
- Shared with dev team: ✅ OK  
- Used for testing: ✅ OK
- Risk level: ⚠️ None (testnet only)

**Future Status**: 🔴 Mainnet Requires New Keys

- Generate fresh keypairs: ✅ Required
- Use hardware wallet: ✅ Recommended
- Set up multisig: ✅ Recommended
- Never reuse devnet keys: ❌ Critical

---

**Remember**: Development keys are for development. Production keys are for production. Never mix them!
