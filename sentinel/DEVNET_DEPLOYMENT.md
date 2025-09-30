# 🚀 Sentinel Program - Devnet Deployment

## ✅ Successfully Deployed to Solana Devnet!

### Deployment Details

**Program ID**: `Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V`

**Deployment Transaction**: `3HZ32jcSPEqELrdUPr6gkKKq8NXHybXvWibn7xCCBf58yoRnPc8ogs3cbjG3ns8jAB9KY9bjGafp1myx1wdoKw8c`

**Network**: Solana Devnet

**RPC Endpoint**: `https://api.devnet.solana.com`

**WebSocket**: `wss://api.devnet.solana.com/`

---

## 🔗 Explorer Links

### Solana Explorer
- **Program**: https://explorer.solana.com/address/Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V?cluster=devnet
- **Deployment TX**: https://explorer.solana.com/tx/3HZ32jcSPEqELrdUPr6gkKKq8NXHybXvWibn7xCCBf58yoRnPc8ogs3cbjG3ns8jAB9KY9bjGafp1myx1wdoKw8c?cluster=devnet

### Solscan
- **Program**: https://solscan.io/account/Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V?cluster=devnet

---

## 📡 RPC Connection Details

### For JavaScript/TypeScript
```javascript
import { Connection, clusterApiUrl } from '@solana/web3.js';

// Using public RPC
const connection = new Connection(clusterApiUrl('devnet'), 'confirmed');

// Or direct URL
const connection = new Connection('https://api.devnet.solana.com', 'confirmed');

// Program ID
const programId = new PublicKey('Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V');
```

### For Anchor
```javascript
import * as anchor from '@coral-xyz/anchor';

const provider = new anchor.AnchorProvider(
  new anchor.web3.Connection('https://api.devnet.solana.com', 'confirmed'),
  wallet,
  { commitment: 'confirmed' }
);

const programId = new anchor.web3.PublicKey('Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V');
```

### For Rust
```rust
use solana_client::rpc_client::RpcClient;
use solana_sdk::pubkey::Pubkey;
use std::str::FromStr;

let rpc_url = "https://api.devnet.solana.com";
let client = RpcClient::new(rpc_url.to_string());
let program_id = Pubkey::from_str("Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V").unwrap();
```

### For CLI
```bash
# Set to devnet
solana config set --url devnet

# Or use direct URL
solana config set --url https://api.devnet.solana.com

# View program
solana program show Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
```

---

## 🎯 Program Instructions

### 1. Initialize
Creates the SentinelCoin mint and mints 100,000 tokens to the deployer.

**Accounts**:
- authority (signer, mut)
- state (PDA, mut)
- sentinel_mint (signer, mut)
- treasury_vault (PDA, mut)
- authority_sentinel_ata (mut)
- treasury_sentinel_ata (mut)
- token_program
- associated_token_program
- system_program
- rent

### 2. Join Network
Pay 1,000 SentinelCoin to join as a peer.

**Accounts**:
- user (signer, mut)
- state (PDA)
- peer (PDA, mut)
- user_sentinel_ata (mut)
- treasury_vault (PDA, mut)
- treasury_sentinel_ata (mut)
- token_program
- system_program

### 3. Mint NFT
Mint a 0-decimal NFT and create a post.

**Accounts**:
- user (signer, mut)
- state (PDA)
- peer (PDA, mut)
- nft_mint (mut)
- user_nft_ata (mut)
- post (PDA, mut)
- token_program
- associated_token_program
- system_program
- rent

**Args**:
- hash: [u8; 32]
- db_addr: Pubkey

### 4. Like NFT
Like a post and increase the owner's karma.

**Accounts**:
- liker (signer, mut)
- state (PDA)
- like (PDA, mut)
- post (PDA, mut)
- liked_peer (PDA, mut)
- liker_peer (PDA)
- system_program

### 5. Finalize Cycle
Distribute 1,000 SentinelCoin to peers based on karma (2-hour cycles).

**Accounts**:
- authority (signer, mut)
- state (PDA, mut)
- sentinel_mint (mut)
- token_program
- remaining_accounts: peer ATAs

**Args**:
- peers: Vec<Pubkey>
- karmas: Vec<u64>

---

## 🔑 PDA Seeds

```
State PDA: ["state"]
Treasury Vault PDA: ["treasury"]
Peer PDA: ["peer", user_pubkey]
Post PDA: ["post", nft_mint_pubkey]
Like PDA: ["like", liker_pubkey, post_pubkey]
```

---

## 💰 Token Details

**Name**: SentinelCoin  
**Decimals**: 9  
**Initial Supply**: 100,000 (minted to deployer on initialize)  
**Mint Authority**: State PDA (for cycle rewards)  
**Join Cost**: 1,000 SentinelCoin  
**Cycle Reward**: 1,000 SentinelCoin per 2-hour cycle  
**Max Per Peer**: 100 SentinelCoin per cycle (10% cap)

---

## 🧪 Testing on Devnet

### Get Devnet SOL
```bash
solana airdrop 2 --url devnet
```

### Check Program
```bash
solana program show Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V --url devnet
```

### Example: Initialize (requires custom client)
You'll need to build a client using the program ID and RPC endpoint above.

---

## 📊 Program Stats

- **Size**: ~313 transactions to deploy
- **Cost**: ~0.5 SOL deployment fee
- **Instructions**: 5 (initialize, join_network, mint_nft, like_nft, finalize_cycle)
- **Accounts**: 4 types (State, PeerState, Post, Like)
- **Errors**: 6 custom error codes

---

## 🔐 Security Features

✅ Overflow protection (checked arithmetic)  
✅ Double-like prevention (PDA uniqueness)  
✅ Peer validation (active status checks)  
✅ Authority-only finalize_cycle  
✅ ATA validation in reward distribution  
✅ Time-gated cycles (2 hours)  
✅ Reward cap (10% per peer)

---

## 📝 Next Steps

1. **Build a Client**
   - Use the RPC endpoint and Program ID above
   - Implement instruction builders for each operation
   - Handle PDA derivation

2. **Test the Program**
   - Initialize the program
   - Join as a peer
   - Mint NFTs
   - Like posts
   - Test cycle finalization (after 2 hours)

3. **Monitor**
   - Use Solana Explorer to view transactions
   - Check program logs for debugging
   - Monitor token balances

4. **Upgrade (if needed)**
   ```bash
   solana program deploy target/deploy/sentinel.so \
     --program-id target/deploy/sentinel-keypair.json \
     --url devnet
   ```

---

## 🆘 Support

- **Program ID**: Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V
- **Network**: Devnet
- **RPC**: https://api.devnet.solana.com
- **Explorer**: https://explorer.solana.com/address/Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V?cluster=devnet

---

## ✅ Deployment Checklist

- [x] Program compiled successfully
- [x] Deployed to Solana Devnet
- [x] Program ID confirmed
- [x] Transaction signature recorded
- [x] Explorer links verified
- [x] RPC endpoint documented
- [x] Ready for client integration

**Status**: 🟢 LIVE ON DEVNET
