# P2P Log Sharing Architecture

## Overview

Each peer runs a simple HTTP server to share their malicious logs. URLs are stored on-chain, enabling direct peer-to-peer access with blockchain-verified integrity.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Peer A (Detector)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Detect attack → generate malicious log             │  │
│  │ 2. Store locally: /data/logs/abc123.log               │  │
│  │ 3. Compute hash: sha256(log)                          │  │
│  │ 4. Start HTTP server on port 9000                     │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 5. Submit to blockchain:                               │  │
│  │    - log_url: "https://peer-a.com:9000/logs/abc123"  │  │
│  │    - file_hash: 0x1234...                             │  │
│  │    - signature: sign(url + hash)                      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                           │
                           │ On-chain Post created
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Peer B (Verifier)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Query blockchain for recent posts                   │  │
│  │ 2. Read Post: log_url, file_hash, uploader            │  │
│  │ 3. Check uploader's karma (trust score)               │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4. Request log from Peer A:                            │  │
│  │    GET https://peer-a.com:9000/logs/abc123            │  │
│  │    Headers:                                            │  │
│  │      X-Peer-Pubkey: <peer_b_pubkey>                   │  │
│  │      X-Timestamp: 1234567890                           │  │
│  │      X-Signature: sign(url + ts + pubkey)             │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 5. Peer A verifies signature → returns log            │  │
│  │ 6. Peer B verifies hash matches on-chain              │  │
│  │ 7. If valid → apply blocks, like post                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────���
```

## Smart Contract Update

```rust
pub struct Post {
    pub owner: Pubkey,
    pub nft_mint: Pubkey,
    pub log_url: String,        // NEW: HTTP URL to log
    pub file_hash: [u8; 32],    // SHA256 of log file
    pub timestamp: i64,
    pub likes: u64,
    pub cycle_index: u64,
}

pub fn mint_nft(
    ctx: Context<MintNft>,
    log_url: String,            // e.g., "https://peer.com:9000/logs/abc123"
    file_hash: [u8; 32],
) -> Result<()> {
    require!(log_url.len() <= 200, SentinelError::UrlTooLong);
    
    // Mint NFT...
    
    let post = &mut ctx.accounts.post;
    post.owner = ctx.accounts.user.key();
    post.nft_mint = ctx.accounts.nft_mint.key();
    post.log_url = log_url;
    post.file_hash = file_hash;
    post.timestamp = Clock::get()?.unix_timestamp;
    post.likes = 0;
    post.cycle_index = ctx.accounts.state.cycle_index;
    
    Ok(())
}
```

## Peer HTTP Server

Simple FastAPI server each peer runs:

```python
# peer_log_server.py
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
import os
import time
import hashlib

app = FastAPI()

LOGS_DIR = "/data/logs"
AUTHORIZED_PEERS = set()  # Load from blockchain

def verify_signature(message: bytes, sig: str, pubkey: str) -> bool:
    # Verify Ed25519 signature
    return pubkey in AUTHORIZED_PEERS

@app.get("/logs/{log_id}")
async def get_log(
    log_id: str,
    x_peer_pubkey: str = Header(...),
    x_timestamp: int = Header(...),
    x_signature: str = Header(...)
):
    # Verify timestamp (5-minute window)
    if abs(time.time() - x_timestamp) > 300:
        raise HTTPException(401, "Request expired")
    
    # Verify peer is authorized
    if x_peer_pubkey not in AUTHORIZED_PEERS:
        raise HTTPException(403, "Not authorized")
    
    # Verify signature
    message = f"{log_id}{x_timestamp}{x_peer_pubkey}".encode()
    if not verify_signature(message, x_signature, x_peer_pubkey):
        raise HTTPException(401, "Invalid signature")
    
    # Return log file
    log_path = os.path.join(LOGS_DIR, f"{log_id}.log")
    if not os.path.exists(log_path):
        raise HTTPException(404, "Log not found")
    
    return FileResponse(log_path)

@app.get("/health")
async def health():
    return {"status": "ok", "logs": len(os.listdir(LOGS_DIR))}
```

## Client Library

```python
# log_client.py
import requests
import hashlib
from solders.keypair import Keypair

class LogClient:
    def __init__(self, keypair: Keypair):
        self.keypair = keypair
        self.pubkey = str(keypair.pubkey())
    
    def download_log(self, log_url: str, expected_hash: str) -> bytes:
        """Download and verify log from peer"""
        timestamp = int(time.time())
        
        # Sign request
        message = f"{log_url}{timestamp}{self.pubkey}".encode()
        signature = str(self.keypair.sign_message(message))
        
        # Request log
        response = requests.get(
            log_url,
            headers={
                'X-Peer-Pubkey': self.pubkey,
                'X-Timestamp': str(timestamp),
                'X-Signature': signature
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to download: {response.status_code}")
        
        # Verify hash
        content = response.content
        actual_hash = hashlib.sha256(content).hexdigest()
        
        if actual_hash != expected_hash:
            raise Exception("Hash mismatch! Log may be corrupted or tampered")
        
        return content
    
    def upload_log(self, log_path: str) -> tuple[str, str]:
        """Upload log to own server and return (url, hash)"""
        # Read log
        with open(log_path, 'rb') as f:
            content = f.read()
        
        # Compute hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Generate log ID
        log_id = hashlib.sha256(content + str(time.time()).encode()).hexdigest()[:16]
        
        # Save locally
        local_path = f"/data/logs/{log_id}.log"
        with open(local_path, 'wb') as f:
            f.write(content)
        
        # Construct URL (use your public IP/domain)
        my_url = os.getenv("MY_PEER_URL", "http://localhost:9000")
        log_url = f"{my_url}/logs/{log_id}"
        
        return log_url, file_hash
```

## Usage Example

### Peer A (Detector):

```python
from log_client import LogClient
from solders.keypair import Keypair

# Initialize
keypair = Keypair.from_base58_string(os.getenv("PEER_PRIVATE_KEY"))
client = LogClient(keypair)

# Upload log
log_url, file_hash = client.upload_log("/data/malicious_logs/attack.log")

# Submit to blockchain
await submit_nft_report(
    log_url=log_url,
    file_hash=file_hash
)

print(f"Report submitted: {log_url}")
```

### Peer B (Verifier):

```python
# Query blockchain for recent reports
posts = await get_recent_posts()

for post in posts:
    # Check uploader's karma
    karma = await get_peer_karma(post.owner)
    
    if karma < 50:
        continue  # Skip low-trust peers
    
    # Download log
    try:
        log_content = client.download_log(post.log_url, post.file_hash)
        
        # Parse and verify
        attackers = parse_log(log_content)
        
        # Apply blocks
        for attacker in attackers:
            block_ip(attacker['ip'])
        
        # Like the post (increase reporter's karma)
        await like_post(post.key)
        
        print(f"Applied {len(attackers)} blocks from {post.owner}")
    
    except Exception as e:
        print(f"Failed to process {post.log_url}: {e}")
```

## Handling Offline Peers

### Problem: What if Peer A goes offline?

**Solution 1: Voluntary Mirrors**
```python
# High-karma peers can mirror popular logs
if post.likes > 10:  # Popular report
    # Download and mirror
    log_content = client.download_log(post.log_url, post.file_hash)
    
    # Store locally
    mirror_url = f"{MY_URL}/mirrors/{post.file_hash[:16]}"
    save_mirror(log_content, mirror_url)
    
    # Optionally: submit mirror URL on-chain
```

**Solution 2: Fallback URLs**
```rust
pub struct Post {
    pub log_url: String,           // Primary URL
    pub mirror_urls: Vec<String>,  // Fallback mirrors
    pub file_hash: [u8; 32],
    // ...
}
```

**Solution 3: Request from Multiple Peers**
```python
# Try primary URL first
try:
    log = client.download_log(post.log_url, post.file_hash)
except:
    # Try mirrors
    for mirror_url in post.mirror_urls:
        try:
            log = client.download_log(mirror_url, post.file_hash)
            break
        except:
            continue
```

## Network Setup

### For Home/Dynamic IP Peers:

**Option 1: Dynamic DNS**
```bash
# Use services like DuckDNS, No-IP
# Update DNS when IP changes
curl "https://www.duckdns.org/update?domains=mypeer&token=xxx&ip="
```

**Option 2: Cloudflare Tunnel**
```bash
# Free tunnel, no port forwarding needed
cloudflared tunnel --url http://localhost:9000
# Gets: https://random-name.trycloudflare.com
```

**Option 3: ngrok**
```bash
ngrok http 9000
# Gets: https://abc123.ngrok.io
```

### For VPS Peers:

```bash
# Just use your public IP/domain
MY_PEER_URL=https://peer.sentinelkarma.io:9000
```

## Security Considerations

### 1. DDoS Protection

```python
# Rate limit per peer
from slowapi import Limiter

limiter = Limiter(key_func=lambda: request.headers.get('X-Peer-Pubkey'))

@app.get("/logs/{log_id}")
@limiter.limit("10/minute")  # 10 requests per minute per peer
async def get_log(...):
    ...
```

### 2. Storage Limits

```python
# Limit log size
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

# Limit total storage
MAX_TOTAL_STORAGE = 1024 * 1024 * 1024  # 1GB

# Auto-delete old logs
def cleanup_old_logs():
    logs = sorted(os.listdir(LOGS_DIR), key=lambda x: os.path.getmtime(x))
    
    total_size = sum(os.path.getsize(f) for f in logs)
    
    while total_size > MAX_TOTAL_STORAGE:
        oldest = logs.pop(0)
        os.remove(oldest)
        total_size -= os.path.getsize(oldest)
```

### 3. Bandwidth Limits

```python
# Track bandwidth per peer
bandwidth_usage = {}  # peer_pubkey -> bytes_sent

@app.get("/logs/{log_id}")
async def get_log(...):
    # Check bandwidth limit
    if bandwidth_usage.get(x_peer_pubkey, 0) > 100 * 1024 * 1024:  # 100MB/day
        raise HTTPException(429, "Bandwidth limit exceeded")
    
    # ... serve file ...
    
    bandwidth_usage[x_peer_pubkey] += file_size
```

## Cost Analysis

### Per Peer:

**Option 1: Home Connection**
- Cost: $0 (use existing internet)
- Bandwidth: Usually sufficient
- Uptime: Depends on your setup

**Option 2: VPS**
- Cost: $5/month (small VPS)
- Bandwidth: 1TB/month included
- Uptime: 99.9%

**Option 3: Cloudflare Tunnel**
- Cost: $0 (free tier)
- Bandwidth: Unlimited
- Uptime: Depends on your local machine

### Network-Wide:

- No central infrastructure needed
- Each peer pays for their own hosting
- Scales naturally with network growth

## Advantages Over IPFS

✅ **Simpler**: Just HTTP + file storage  
✅ **Faster**: Direct peer-to-peer, no DHT  
✅ **Cheaper**: No IPFS infrastructure  
✅ **More Control**: Peers manage their data  
✅ **Better Performance**: Local disk > IPFS  
✅ **Easier Debug**: Standard HTTP logs  
✅ **Flexible**: Can use any hosting (home, VPS, cloud)  

## Summary

**Architecture:**
- Each peer runs simple HTTP server
- URLs stored on blockchain
- Direct P2P with signed requests
- Hash verification ensures integrity
- Optional mirrors for high-availability

**Result:**
- True decentralization
- Simple implementation
- Low cost
- High performance
- Verifiable integrity
