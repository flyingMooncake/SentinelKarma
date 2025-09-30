# 🔐 Sentinel Program - Private Keys

## ⚠️ SECURITY WARNING
**NEVER share these private keys publicly!**  
**Keep this file secure and private!**

---

## 1️⃣ Your Wallet (Deployer/Authority)

### Private Key (Byte Array)
```json
[122,32,178,110,110,158,62,31,165,41,32,203,54,15,176,242,141,248,136,2,452,371,216,98,255,247,224,169,91,79,232,31,149,253,136,210,150,192,146,62,471,351,981,492,065,419,414,817,881,177]
```

### Public Key (Address)
```bash
# Get your public key
solana address
```

### How to Import in JavaScript
```javascript
import { Keypair } from '@solana/web3.js';
import fs from 'fs';

// Load from file
const keypairData = JSON.parse(fs.readFileSync('/home/water/.config/solana/id.json', 'utf-8'));
const wallet = Keypair.fromSecretKey(Uint8Array.from(keypairData));

console.log('Public Key:', wallet.publicKey.toString());
```

### How to Import in Phantom/Solflare
1. Open wallet
2. Click "Add/Import Account"
3. Select "Import Private Key"
4. Paste the byte array above (as comma-separated numbers)

---

## 2️⃣ Program Keypair (Upgrade Authority)

### Program ID (Public Key)
```
Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
```

### Private Key (Byte Array)
```json
[43,238,58,183,217,31,215,44,93,42,117,61,47,228,216,170,121,102,227,252,86,125,195,72,4,196,102,51,121,84,92,63,77,39,46,111,87,85,238,29,196,244,30,85,205,162,161,156,0,150,191,241,246]
```

### How to Use in JavaScript
```javascript
import { Keypair, PublicKey } from '@solana/web3.js';
import fs from 'fs';

// Load program keypair
const programKeypairData = JSON.parse(
  fs.readFileSync('/home/water/sentinel/target/deploy/sentinel-keypair.json', 'utf-8')
);
const programKeypair = Keypair.fromSecretKey(Uint8Array.from(programKeypairData));

console.log('Program ID:', programKeypair.publicKey.toString());
// Output: Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
```

---

## 🔄 Convert to Base58 (Phantom Format)

### For Your Wallet
```bash
# Install bs58 if needed
npm install -g bs58-cli

# Convert to base58
cat ~/.config/solana/id.json | jq -r '.' | bs58 encode
```

### Using Node.js
```javascript
import bs58 from 'bs58';
import fs from 'fs';

// Wallet
const walletData = JSON.parse(fs.readFileSync('/home/water/.config/solana/id.json', 'utf-8'));
const walletBase58 = bs58.encode(Buffer.from(walletData));
console.log('Wallet Private Key (Base58):', walletBase58);

// Program
const programData = JSON.parse(fs.readFileSync('/home/water/sentinel/target/deploy/sentinel-keypair.json', 'utf-8'));
const programBase58 = bs58.encode(Buffer.from(programData));
console.log('Program Private Key (Base58):', programBase58);
```

---

## 📱 Import to Wallets

### Phantom Wallet
1. Open Phantom
2. Settings → Add/Import Account
3. Import Private Key
4. Paste the byte array or base58 string

### Solflare
1. Open Solflare
2. Add Account → Import Private Key
3. Paste the private key

### Backpack
1. Open Backpack
2. Settings → Import Wallet
3. Paste the private key

---

## 🔧 Export Keys to Different Formats

### Create a conversion script
```javascript
// save as convert-keys.js
import bs58 from 'bs58';
import fs from 'fs';

// Wallet
const walletBytes = JSON.parse(fs.readFileSync(process.env.HOME + '/.config/solana/id.json', 'utf-8'));
console.log('=== WALLET ===');
console.log('Byte Array:', JSON.stringify(walletBytes));
console.log('Base58:', bs58.encode(Buffer.from(walletBytes)));
console.log('Hex:', Buffer.from(walletBytes).toString('hex'));

// Program
const programBytes = JSON.parse(fs.readFileSync('./target/deploy/sentinel-keypair.json', 'utf-8'));
console.log('\n=== PROGRAM ===');
console.log('Byte Array:', JSON.stringify(programBytes));
console.log('Base58:', bs58.encode(Buffer.from(programBytes)));
console.log('Hex:', Buffer.from(programBytes).toString('hex'));
```

Run:
```bash
node convert-keys.js
```

---

## 🛡️ Security Best Practices

### ✅ DO:
- Keep these keys in a secure password manager
- Use hardware wallets for mainnet
- Backup keys in multiple secure locations
- Use environment variables in production
- Rotate keys regularly

### ❌ DON'T:
- Share keys publicly
- Commit keys to git repositories
- Store keys in plain text on servers
- Use the same keys for testnet and mainnet
- Share screenshots containing keys

---

## 🔐 Backup Your Keys

### Create Encrypted Backup
```bash
# Encrypt wallet key
gpg -c ~/.config/solana/id.json

# Encrypt program key
gpg -c target/deploy/sentinel-keypair.json

# Store the .gpg files securely
```

### Decrypt When Needed
```bash
gpg -d id.json.gpg > id.json
```

---

## 📋 Key Locations

### Wallet Keypair
```
/home/water/.config/solana/id.json
```

### Program Keypair
```
/home/water/sentinel/target/deploy/sentinel-keypair.json
```

### Program ID (Public)
```
Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
```

---

## 🔄 Upgrade Program (Using Program Keypair)

```bash
# Build new version
anchor build --no-idl

# Deploy upgrade
solana program deploy target/deploy/sentinel.so \
  --program-id target/deploy/sentinel-keypair.json \
  --url devnet
```

---

## ⚠️ IMPORTANT NOTES

1. **Program Keypair** = Upgrade authority for the program
2. **Wallet Keypair** = Your personal wallet (deployer/authority)
3. Both are needed for different operations
4. **NEVER** share these keys with anyone
5. For mainnet, use a hardware wallet or multisig

---

## 🆘 If Keys Are Compromised

### Wallet Compromised:
1. Create new wallet immediately
2. Transfer all assets to new wallet
3. Update program authority to new wallet

### Program Compromised:
1. Deploy new program with new keypair
2. Migrate users to new program
3. Close old program if possible

---

**Remember: These keys control your funds and program. Keep them safe!** 🔒
