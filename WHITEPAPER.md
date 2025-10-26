# SentinelKarma: Decentralized Network Telemetry and Reputation System

**Version 2.0**  
**Date: January 2025**

---

## Abstract

SentinelKarma is a decentralized threat intelligence network for Web3 RPC infrastructure that combines real-time statistical anomaly detection with blockchain-based reputation mechanics. The system addresses critical challenges in distributed network security: detecting malicious behavior, incentivizing quality reporting, and creating a sustainable peer-operated monitoring ecosystem.

By integrating off-chain telemetry analysis with on-chain reputation tokens and peer-to-peer log sharing, SentinelKarma creates a self-sustaining network where operators are economically incentivized to maintain high-quality monitoring standards. The system employs statistical process control, MQTT-based messaging, HTTP-based P2P log distribution, and Solana smart contracts to deliver a comprehensive solution for network security.

**Key Innovation**: Unlike traditional centralized monitoring or complex IPFS-based systems, SentinelKarma uses simple peer-to-peer HTTP log sharing with blockchain-verified integrity, making it accessible, affordable, and verifiable.

---

## 1. Introduction

### 1.1 Problem Statement

Modern Web3 infrastructure faces critical security challenges:

1. **RPC Abuse**: Malicious actors exploit public endpoints through excessive requests, resource-intensive queries, and coordinated attacks
2. **Lack of Accountability**: Anonymous access makes it difficult to identify and mitigate bad actors
3. **Monitoring Gaps**: Centralized monitoring creates single points of failure and trust dependencies
4. **Incentive Misalignment**: Network operators lack economic incentives to share threat intelligence
5. **Data Silos**: Security information remains fragmented across individual operators
6. **High Infrastructure Costs**: Complex distributed storage (IPFS) creates barriers to entry

### 1.2 Solution Overview

SentinelKarma introduces a three-layer architecture with simplified P2P data sharing:

**Layer 1: Telemetry Collection & Analysis**
- Real-time event stream processing from RPC endpoints
- Statistical anomaly detection using z-scores and percentile analysis
- Automated classification of normal vs. malicious traffic patterns
- 30-second rotation for malicious logs, 30-minute for normal logs

**Layer 2: Distributed Messaging & Storage**
- MQTT-based publish/subscribe for real-time alerts
- Simple HTTP-based peer-to-peer log sharing
- Each peer runs their own log server (FastAPI)
- Direct peer-to-peer communication without central infrastructure
- Signed requests for authentication and authorization

**Layer 3: Blockchain Reputation & Verification**
- Non-transferable Karma Points (KP) for peer reputation
- Fungible SEKA tokens convertible from earned karma
- On-chain log URL and hash storage for verification
- Community validation through likes
- Automated NFT minting for detected threats

---

## 2. System Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     RPC Network Layer                        │
│  (Solana RPC Endpoints, Web3 Infrastructure)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Telemetry Collection                        │
│  • Event Stream (JSONL)                                     │
│  • Request/Response Logging                                 │
│  • Metadata Extraction (IP, Method, Latency, Errors)       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Statistical Analysis                        │
│  • Rolling Window Aggregation (250ms default)               │
│  • P95 Latency Calculation                                  │
│  • Error Rate Computation                                   │
│  • Z-Score Anomaly Detection                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  MQTT Message Broker                         │
│  • Topic: sentinel/diag                                     │
│  • Real-time Alert Distribution                             │
│  • Pub/Sub Architecture                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Classification & Storage                        │
│  • Threshold-based Classification                           │
│  • Malicious Logs (30-sec rotation)                        │
│  • Normal Logs (30-min rotation)                           │
│  • Local HTTP Server (FastAPI)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              P2P Log Sharing (HTTP)                          │
│  • Each peer runs own log server                            │
│  • Signed requests for authentication                       │
│  • Direct peer-to-peer downloads                            │
│  • Hash verification from blockchain                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Blockchain Layer (Solana)                   │
│  • NFT-based Report Submission                              │
│  • Log URL + Hash Storage                                   │
│  • Karma Point Accumulation                                 │
│  • SEKA Token Conversion                                    │
│  • Network Membership Management                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**Event Processing Pipeline:**

1. **Ingestion**: RPC requests logged as JSONL events with metadata (timestamp, IP hash, method, latency, error status)
2. **Windowing**: Events aggregated into rolling time windows (default 250ms)
3. **Metrics**: Per-window calculation of p95 latency, error rate, request count
4. **Anomaly Detection**: Z-score computation against historical baselines
5. **Classification**: Events exceeding thresholds routed to malicious logs
6. **Distribution**: Diagnostic messages published to MQTT for peer consumption
7. **Storage**: Logs stored locally and served via HTTP
8. **Auto-Mint**: Daemon monitors for new malicious logs and mints NFTs
9. **Reporting**: NFT contains log URL and hash on blockchain
10. **Verification**: Peers download logs with signed requests, verify hash
11. **Reputation**: Community validation through likes accumulates karma
12. **Conversion**: Karma converted to SEKA tokens for economic utility

---

## 3. Telemetry & Anomaly Detection

### 3.1 Event Schema

Each RPC event is captured with the following structure:

```json
{
  "ts": 1755944583,
  "ip_hash": "44f8aab55b43",
  "method": "getLogs",
  "latency_ms": 274.41,
  "error": false,
  "region": "eu-central",
  "asn": 64512
}
```

### 3.2 Statistical Metrics

**Per-Window Aggregation:**

- **P95 Latency**: 95th percentile response time (ms)
- **Error Rate**: Ratio of failed requests (0.0 - 1.0)
- **Request Count**: Total events in window
- **Method Distribution**: Breakdown by RPC method type

**Z-Score Calculation:**

```
z_latency = (current_p95 - historical_mean) / historical_stddev
z_error = (current_error_rate - historical_mean) / historical_stddev
```

### 3.3 Classification Thresholds

Events are classified as malicious if **any** condition is met:

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Error Rate | ≥ 5% | Indicates scanning, fuzzing, or invalid requests |
| P95 Latency | ≥ 250ms | Resource exhaustion or heavy query abuse |
| Z-Score (Latency) | ≥ 4.0 | Statistical outlier indicating anomalous behavior |
| Z-Score (Error) | ≥ 2.0 | Unusual error patterns suggesting attacks |

### 3.4 Log Rotation

**Malicious Logs:**
- Rotation: Every 30 seconds
- Retention: Indefinite (for NFT minting)
- Format: `YYYYMMDD_HHMMSS.jsonl`
- Location: `data/malicious_logs/`

**Normal Logs:**
- Rotation: Every 30 minutes
- Retention: 2 hours (configurable)
- Format: `YYYYMMDD_HHMM.jsonl`
- Location: `data/logs_normal/`

### 3.5 Heavy Method Detection

Certain RPC methods are computationally expensive and monitored separately:

- `getProgramAccounts`: Full account scans
- `getLogs`: Historical log queries
- `getSignaturesForAddress`: Transaction history enumeration

Burst detection triggers when heavy methods exceed baseline rates by 3x within a 60-second window.

---

## 4. Distributed Messaging Layer

### 4.1 MQTT Architecture

**Broker Configuration:**
- Protocol: MQTT v3.1.1
- Port: 1883 (unencrypted for MVP)
- Persistence: Disabled (real-time only)
- Anonymous Access: Enabled (dev environment)

**Topic Structure:**
```
sentinel/
  ├── diag              # Diagnostic messages (all peers)
  ├── region/eu-central # Regional filtering
  ├── asn/64512         # ASN-specific alerts
  └── method/getLogs    # Method-specific monitoring
```

### 4.2 Message Format

Published diagnostic messages follow this schema:

```json
{
  "ts": 1755944583,
  "window_ms": 250,
  "region": "eu-central",
  "asn": 64512,
  "method": "getLogs",
  "metrics": {
    "p95": 274.41,
    "err_rate": 0.05
  },
  "z": {
    "lat": 12.53,
    "err": 2.1
  },
  "sample": "iphash:44f8aab55b43"
}
```

### 4.3 Scalability Considerations

- **QoS Level 0**: Fire-and-forget for maximum throughput
- **No Persistence**: Reduces broker memory footprint
- **Topic Filtering**: Subscribers receive only relevant alerts
- **Horizontal Scaling**: Multiple broker instances with load balancing (future)

---

## 5. Peer-to-Peer Log Sharing

### 5.1 Architecture Overview

SentinelKarma uses a simple peer-to-peer HTTP architecture for off-chain log storage. Each peer runs their own log server and shares URLs via the blockchain.

**Key Benefits:**
- **Simple**: Just HTTP + file storage (no IPFS complexity)
- **Fast**: Direct peer-to-peer (no DHT lookups)
- **Cheap**: $0-5/month per peer (vs $25-50 for IPFS)
- **Controlled**: Peers manage their own data
- **Flexible**: Works with home connection, VPS, or cloud
- **Verifiable**: Hash on blockchain proves integrity

### 5.2 Access Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Peer A (Detector)                                           │
│ 1. Detects attack → generates malicious log                │
│ 2. Stores locally: data/malicious_logs/20250115_143022.jsonl│
│ 3. Computes SHA256 hash                                     │
│ 4. Mints NFT with: {log_url, file_hash}                    │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼ (blockchain)
┌─────────────────────────────────────────────────────────────┐
│ Blockchain (Solana)                                         │
│ Post Account:                                               │
│   - log_url: "http://peer-a.com:9000/logs/abc123"         │
│   - file_hash: "sha256:..."                                │
│   - owner: Peer A pubkey                                   │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼ (read)
┌─────────────────────────────────────────────────────────────┐
│ Peer B (Verifier)                                           │
│ 1. Reads Post account from blockchain                       │
│ 2. Gets log_url and file_hash                              │
│ 3. Creates signed request:                                  │
│    sign(log_url + timestamp + pubkey)                      │
│ 4. Requests log from Peer A's server                       │
│ 5. Peer A verifies signature → returns log                 │
│ 6. Peer B verifies hash matches blockchain                 │
│ 7. If valid → applies blocks, likes post                   │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Log Server API

**FastAPI HTTP Server (Port 9000)**

```python
# Upload log (internal use)
POST /logs
Body: multipart/form-data with log file
Returns: {log_id, log_url, file_hash}

# Download log (requires signature)
GET /logs/{log_id}
Headers:
  X-Peer-Pubkey: <base58_pubkey>
  X-Timestamp: <unix_timestamp>
  X-Signature: <ed25519_signature>
Returns: log file content

# Get metadata
GET /logs/{log_id}/metadata
Returns: {filename, size, hash, timestamp}

# Health check
GET /health
Returns: {status, logs_stored, storage_used}

# Statistics
GET /stats
Returns: {total_logs, total_size, bandwidth_usage}
```

### 5.4 Security Features

**Authentication:**
- Ed25519 signatures prove peer identity
- Signature format: `sign(log_url + timestamp + pubkey)`
- Public key verified against blockchain

**Authorization:**
- Only active network members can request logs
- Authorized peers list synced from smart contract
- Automatic peer list updates every 5 minutes

**Replay Protection:**
- Timestamp validation (5-minute window)
- Prevents replay attacks
- Rejects stale requests

**Integrity:**
- SHA256 hash stored on blockchain
- Downloaded log verified against hash
- Tampered logs rejected automatically

**Rate Limiting:**
- 100MB/day per peer (configurable)
- 10MB max per log file
- 1GB total storage limit
- Automatic cleanup of old logs

**Audit Trail:**
- All access attempts logged
- IP addresses, timestamps, signatures
- Failed authentication tracked
- Bandwidth usage monitored

### 5.5 Implementation

**Log Server (Python FastAPI):**
```python
from fastapi import FastAPI, Header, HTTPException
from solders.signature import Signature
from solders.pubkey import Pubkey
import hashlib

app = FastAPI()

@app.get("/logs/{log_id}")
async def download_log(
    log_id: str,
    x_peer_pubkey: str = Header(...),
    x_timestamp: int = Header(...),
    x_signature: str = Header(...)
):
    # 1. Verify timestamp (5-minute window)
    if abs(time.time() - x_timestamp) > 300:
        raise HTTPException(401, "Timestamp expired")
    
    # 2. Verify signature
    message = f"{log_id}{x_timestamp}{x_peer_pubkey}"
    pubkey = Pubkey.from_string(x_peer_pubkey)
    sig = Signature.from_string(x_signature)
    if not sig.verify(pubkey, message.encode()):
        raise HTTPException(401, "Invalid signature")
    
    # 3. Check authorization
    if not is_authorized_peer(pubkey):
        raise HTTPException(403, "Not authorized")
    
    # 4. Return log file
    return FileResponse(f"data/logs/{log_id}")
```

**Client (Python):**
```python
from solders.keypair import Keypair
import requests

def download_log(log_url: str, keypair: Keypair):
    timestamp = int(time.time())
    message = f"{log_url}{timestamp}{str(keypair.pubkey())}"
    signature = keypair.sign_message(message.encode())
    
    headers = {
        "X-Peer-Pubkey": str(keypair.pubkey()),
        "X-Timestamp": str(timestamp),
        "X-Signature": str(signature)
    }
    
    response = requests.get(log_url, headers=headers)
    return response.content
```

---

## 6. Blockchain Reputation System

### 6.1 Token Economics

**Dual-Token Model:**

1. **Karma Points (KP)**: Non-transferable reputation metric
   - Earned through community validation (likes on reports)
   - Accumulated per 2-hour cycle
   - Stored on-chain in PeerState accounts
   - Reset after each cycle finalization

2. **SEKA Token**: Fungible SPL token
   - Conversion rate: 100 KP = 1 SEKA
   - Decimals: 9 (standard SPL)
   - Use cases: Network membership, governance, rewards
   - Total supply: Dynamic (minted through karma conversion)

**Initial Distribution:**
- 100,000 SEKA minted at initialization
- Distributed to project authority for ecosystem bootstrapping
- Ongoing minting through karma conversion only

### 6.2 Karma Accumulation

**Earning Mechanisms:**

1. **Report Submission**: Peers mint NFTs representing threat reports
   - NFT metadata includes log URL and file hash
   - On-chain reference to database address
   - Timestamped with cycle index
   - Automatic minting via daemon

2. **Community Validation**: Other peers "like" quality reports
   - Each like increments post owner's karma by 1
   - Likers must be active network members
   - Double-liking prevented via PDA uniqueness
   - Verification requires downloading and validating log

3. **Cycle Finalization**: Authority distributes proportional rewards
   - Total pool: 1,000 SEKA per 2-hour cycle
   - Distribution: Proportional to karma earned
   - Per-peer cap: 10% of cycle pool (100 SEKA max)
   - Karma reset after distribution

**Formula:**
```
peer_reward = min(
  (peer_karma / total_karma) * 1000 SEKA,
  100 SEKA
)
```

### 6.3 Network Membership

**Joining Requirements:**
- Payment: 1,000 SEKA (1 SEKA with 9 decimals)
- Creates PeerState account (active=true)
- Enables report submission and liking privileges
- Adds peer to authorized list for log access

**Benefits:**
- Submit threat reports as NFTs
- Validate others' reports (earn karma)
- Download logs from other peers
- Participate in governance (future)
- Access premium RPC tiers (future)

### 6.4 Smart Contract Architecture

**Program ID:** `Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V`

**Account Structure:**

```rust
State (PDA: ["state"])
├── authority: Pubkey
├── sentinel_mint: Pubkey
├── treasury_vault: Pubkey
├── cycle_start_ts: i64
└── cycle_index: u64

PeerState (PDA: ["peer", user_pubkey])
├── user: Pubkey
├── active: bool
└── karma: u64

Post (PDA: ["post", nft_mint])
├── owner: Pubkey
├── nft_mint: Pubkey
├── hash: [u8; 32]        // SHA256 of log file
├── db_addr: Pubkey       // Database reference
├── likes: u64
└── cycle_index: u64

Like (PDA: ["like", liker, post])
├── liker: Pubkey
└── post: Pubkey
```

**Key Instructions:**

1. `initialize`: Deploy contract, mint initial supply, set mint authority
2. `join_network`: Pay 1000 SEKA fee, activate peer membership
3. `mint_nft(hash, db_addr)`: Submit threat report as NFT with log hash
4. `like_nft`: Validate report, increment karma
5. `finalize_cycle`: Distribute SEKA rewards proportionally
6. `reset_karma`: Reset all peer karma for new cycle

---

## 7. Automated NFT Minting

### 7.1 Auto-Mint Daemon

**Purpose**: Automatically monitor for new malicious logs and mint NFTs

**Configuration** (`scripts/auto_mint.conf`):
```bash
CHECK_INTERVAL=30          # Check every 30 seconds
FILE_AGE_MINUTES=60        # Process files older than 60 minutes
MALICIOUS_DIR=/data/malicious_logs
CONTRACT_DIR=/data/contract_data
WALLET_PATH=~/.config/solana/id.json
RPC_URL=http://localhost:8899
```

**Process Flow:**
1. Monitor `data/malicious_logs/` directory
2. Detect new `.jsonl` files older than threshold
3. Compute SHA256 hash of file content
4. Upload to local log server
5. Mint NFT with log URL and hash
6. Save mapping to `nft_mappings.json`
7. Mark file as processed

**NFT Mapping Format:**
```json
{
  "filename": "20250115_143022.jsonl",
  "log_url": "http://localhost:9000/logs/abc123",
  "hash": "sha256:...",
  "nft_tx": "5xK7...",
  "timestamp": 1705329622
}
```

### 7.2 NFT Sync Daemon

**Purpose**: Continuously sync NFT mappings from blockchain

**Process:**
1. Query Solana for all transactions from wallet
2. Filter for `mint_nft` instructions
3. Extract log URL, hash, and timestamp
4. Update `nft_mappings.json`
5. Refresh every 30 seconds

**Benefits:**
- Web dashboard shows real-time NFT data
- Peers can discover all minted reports
- Blockchain serves as source of truth
- Automatic synchronization

---

## 8. Web Dashboard

### 8.1 Architecture

**Technology Stack:**
- **Frontend**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: shadcn/ui + Tailwind CSS
- **Charts**: Recharts
- **State**: React Hooks
- **API**: Fetch API with proxy

**Components:**
- `DashboardOverview`: System status and latest NFTs
- `NFTsPanel`: All minted NFTs with filtering
- `LiveAlertsPanel`: Real-time MQTT alerts
- `FraudulentIPsPanel`: Detected malicious IPs
- `SystemInfoPanel`: Server health and configuration

### 8.2 API Integration

**Proxy Configuration** (`vite.config.ts`):
```typescript
proxy: {
  '/api/logs': {
    target: 'http://log-server:9000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/logs/, '')
  },
  '/api/solana': {
    target: 'http://localhost:8899',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/solana/, '')
  }
}
```

**API Service** (`services/api.ts`):
```typescript
export const dashboardAPI = {
  async getOverview() {
    const [health, stats, nftCount, slot] = await Promise.all([
      logServerAPI.getHealth(),
      logServerAPI.getStats(),
      nftAPI.getTotalMinted(),
      solanaAPI.getSlot()
    ]);
    return { logServer, nfts, solana };
  }
};
```

### 8.3 Real-time Updates

- Dashboard refreshes every 30 seconds
- NFT list updates automatically
- Health checks every 10 seconds
- Live alert streaming (future: WebSocket)

---

## 9. Security & Privacy

### 9.1 Privacy Protections

**IP Address Hashing:**
- Source IPs salted and hashed before logging
- Salt configurable per deployment
- Prevents correlation across datasets
- Enables abuse detection without PII exposure

**Data Minimization:**
- Only essential metadata captured
- No request/response bodies logged
- Geographic data limited to region/ASN
- Retention policies enforce automatic deletion

### 9.2 Access Control

**Log Server Security:**
- Ed25519 signature verification on every request
- Authorized peers list synced from blockchain
- Timestamp validation (5-minute window)
- Rate limiting (100MB/day per peer)
- Storage limits (1GB total, 10MB per log)
- Automatic cleanup of old logs

**Smart Contract Security:**
- PDA-based access control
- Overflow checks on all arithmetic
- Constraint validation on all accounts
- Mint authority delegated to program PDA
- Active peer requirement for all interactions

### 9.3 Attack Resistance

**Sybil Resistance:**
- Network membership requires 1000 SEKA payment
- Economic cost to create multiple identities
- Karma accumulation requires community validation
- Per-peer reward caps limit single-actor dominance

**Spam Prevention:**
- Like PDAs prevent double-liking
- Active peer requirement for all interactions
- Cycle-based reward distribution limits gaming
- Authority-controlled finalization prevents premature claims

**Log Integrity:**
- SHA256 hash stored on blockchain
- Downloaded logs verified against hash
- Tampered logs rejected automatically
- Audit trail of all access attempts

### 9.4 Production Hardening (Roadmap)

**MQTT Security:**
- TLS encryption (port 8883)
- Username/password authentication
- ACL-based topic permissions
- VPN or private network deployment

**Log Server Security:**
- HTTPS with SSL certificates
- DDoS protection (Cloudflare/AWS Shield)
- Automatic peer list sync from contract
- Bandwidth monitoring and alerts
- Geographic distribution (CDN)

---

## 10. Performance & Scalability

### 10.1 Throughput Metrics

**Telemetry Processing:**
- Event ingestion: 10,000 events/second per agent
- Window aggregation: 250ms latency
- MQTT publishing: <10ms per message
- Classification: Real-time (no backlog)

**Log Server:**
- Upload: 10MB/s (limited by disk I/O)
- Download: 100MB/s (limited by network)
- Concurrent connections: 100 peers
- Storage: 1GB total, auto-cleanup

**Blockchain Operations:**
- Report submission: ~400ms (Solana block time)
- Like transaction: ~400ms
- Cycle finalization: ~2s for 100 peers
- Gas costs: ~0.001 SOL per transaction

### 10.2 Scaling Strategies

**Horizontal Scaling:**
- Multiple agent instances per region
- MQTT broker clustering with shared subscriptions
- Sharded log storage by time/region
- Parallel cycle finalization for large peer sets
- CDN for popular logs (future)

**Optimization Techniques:**
- Batch MQTT publishing (10 messages/batch)
- Compressed log rotation (gzip)
- Bloom filters for duplicate detection
- Lazy PDA initialization (on-demand account creation)
- Incremental hash computation

---

## 11. Use Cases & Applications

### 11.1 RPC Provider Protection

**Scenario**: Public Solana RPC endpoint experiencing abuse

**Solution**:
1. Deploy SentinelKarma agent monitoring request stream
2. Detect anomalous patterns (high error rates, heavy methods)
3. Receive real-time MQTT alerts on threshold breaches
4. Malicious logs stored locally and served via HTTP
5. Auto-mint daemon creates NFT with log URL and hash
6. Other peers download and verify logs (signed requests)
7. Implement rate limiting based on validated threat intelligence

**Outcome**: 70% reduction in abusive traffic, improved service quality, shared threat intelligence

### 11.2 Collaborative Threat Intelligence

**Scenario**: Multiple RPC providers want to share security data

**Solution**:
1. Each provider runs SentinelKarma agent + log server
2. Malicious logs stored locally, served via HTTP
3. Auto-mint daemon submits NFT reports with log URL
4. Other peers download logs with signed requests
5. Community validates reports through likes
6. High-karma reports automatically trusted
7. Validated threats distributed across network

**Outcome**: Faster threat detection, reduced monitoring costs, collective defense

**P2P Sharing Example:**
```python
# Peer A: Auto-mint daemon uploads malicious log
from infra.log_server.client import LogClient

client = LogClient(keypair)
log_url, file_hash = client.upload_log('/data/malicious_logs/attack.log')
mint_nft(file_hash, db_addr)  # Automatic

# Peer B: Verify and like
post = get_post(post_id)
log_content = client.download_log(post.log_url, post.file_hash)
if verify_threat(log_content):
    like_nft(post)  # Earn karma
```

### 11.3 Security Research

**Scenario**: Researchers studying RPC attack patterns

**Solution**:
1. Deploy monitoring agents across multiple regions
2. Collect real-world attack data
3. Analyze patterns and techniques
4. Share findings via NFT reports
5. Contribute to Web3 security knowledge

**Outcome**: Better understanding of threats, improved defenses, academic publications

---

## 12. Roadmap

### Q1 2025: MVP Launch ✅
- ✅ Core telemetry pipeline
- ✅ MQTT messaging layer
- ✅ Smart contracts deployed
- ✅ NFT-based reporting
- ✅ Karma accumulation
- ✅ P2P HTTP log sharing
- ✅ Auto-mint daemon
- ✅ Web dashboard

### Q2 2025: Production Hardening
- [ ] TLS-encrypted MQTT
- [ ] HTTPS log server with SSL
- [ ] Advanced anomaly detection (ML models)
- [ ] Multi-region deployment
- [ ] Security audit
- [ ] Performance optimization
- [ ] CDN integration for logs

### Q3 2025: Ecosystem Growth
- [ ] Public testnet launch
- [ ] Developer documentation
- [ ] SDK for RPC providers
- [ ] Mobile monitoring app
- [ ] Community onboarding program
- [ ] Partnership with RPC providers

### Q4 2025: Decentralization
- [ ] Multisig governance
- [ ] Permissionless peer joining
- [ ] Cross-chain bridge (Ethereum, Polygon)
- [ ] Mainnet launch
- [ ] Token listing
- [ ] DAO formation

### 2026: Advanced Features
- [ ] On-chain DAO governance
- [ ] Adaptive threshold algorithms
- [ ] Predictive threat modeling
- [ ] Automated response actions
- [ ] Enterprise partnerships
- [ ] Global CDN network

---

## 13. Technical Specifications

### 13.1 System Requirements

**Agent Deployment:**
- OS: Linux (Ubuntu 20.04+), Docker support
- CPU: 2 cores minimum
- RAM: 4GB minimum
- Storage: 100GB SSD (log retention)
- Network: 100Mbps, low latency to MQTT broker

**Log Server:**
- Python 3.11+ (FastAPI)
- CPU: 1 core minimum
- RAM: 1GB minimum
- Storage: 10GB SSD (local logs)
- Network: 100Mbps, public IP or tunnel

**MQTT Broker:**
- Mosquitto 2.0+
- CPU: 4 cores
- RAM: 8GB
- Network: 1Gbps, public IP or VPN

**Web Dashboard:**
- Node.js 20+
- Nginx or similar web server
- CPU: 1 core
- RAM: 512MB
- Network: 100Mbps

**Blockchain Node:**
- Solana RPC endpoint (devnet/mainnet)
- Anchor framework 0.28+
- Rust 1.70+

### 13.2 Configuration Parameters

```bash
# Telemetry Agent
WINDOW_MS=250              # Aggregation window
Z_THRESHOLD=3.0            # Anomaly detection sensitivity
METHODS_HEAVY=getProgramAccounts,getLogs
SALT=random-secret-value   # IP hashing salt

# Classification
ERR_THR=0.05              # 5% error rate threshold
P95_THR=250               # 250ms latency threshold
ZLAT_THR=4.0              # Latency z-score
ZERR_THR=2.0              # Error z-score

# Rotation
MAL_WINDOW_MIN=0.5        # Malicious log rotation (30 seconds)
NOR_WINDOW_MIN=30         # Normal log rotation (30 minutes)

# Log Server
SERVER_HOST=0.0.0.0
SERVER_PORT=9000
MY_PEER_URL=https://my-peer.com:9000
LOGS_DIR=/data/logs
AUTHORIZED_PEERS_FILE=/data/authorized_peers.txt
MAX_LOG_SIZE=10485760     # 10MB
MAX_STORAGE=1073741824    # 1GB

# Auto-Mint
CHECK_INTERVAL=30         # Check every 30 seconds
FILE_AGE_MINUTES=60       # Process files older than 60 min

# Blockchain
CYCLE_SECONDS=7200        # 2-hour cycles
JOIN_COST=1000000000000   # 1,000 SEKA (with 9 decimals)
CYCLE_REWARD_TOTAL=1000000000000  # 1,000 SEKA per cycle
MAX_PEER_REWARD_PCT=10    # 10% cap per peer
```

### 13.3 API Reference

**MQTT Topics:**
```
sentinel/diag              # All diagnostic messages
sentinel/region/{region}   # Regional filtering
sentinel/asn/{asn}         # ASN-specific
sentinel/method/{method}   # Method-specific
```

**Log Server API:**
```http
POST /logs
Headers:
  X-Peer-Pubkey: ABC123...
  X-Timestamp: 1234567890
  X-Signature: signature_here
Body: multipart/form-data with log file

GET /logs/{log_id}
Headers:
  X-Peer-Pubkey: ABC123...
  X-Timestamp: 1234567890
  X-Signature: signature_here

GET /logs/{log_id}/metadata
GET /health
GET /stats
```

**Smart Contract Instructions:**
```rust
initialize(authority)
join_network(user, payment)
mint_nft(user, hash, db_addr)
like_nft(liker, post)
finalize_cycle(authority, peers, karmas)
reset_karma(authority)
```

---

## 14. Conclusion

SentinelKarma represents a paradigm shift in Web3 infrastructure monitoring by combining real-time telemetry, simple peer-to-peer log sharing, and blockchain-based reputation into a cohesive, accessible system. The architecture addresses critical gaps in current solutions:

1. **Decentralization**: No single point of failure or trust
2. **Simplicity**: HTTP-based P2P sharing instead of complex IPFS
3. **Affordability**: $0-5/month per peer vs $25-50 for IPFS
4. **Incentive Alignment**: Economic rewards for quality monitoring
5. **Real-time Response**: Sub-second anomaly detection and alerting
6. **Community-Driven**: Peer validation ensures data quality
7. **Verifiable**: Blockchain hashes prove log integrity
8. **Sustainable**: Self-funding through membership fees and token economics

**Key Innovation**: By using simple HTTP-based peer-to-peer log sharing with blockchain-verified integrity, SentinelKarma makes decentralized threat intelligence accessible to everyone—from individual developers to large RPC providers—without the complexity and cost of traditional distributed storage systems.

As the Web3 ecosystem continues to grow, the need for robust, decentralized monitoring infrastructure becomes increasingly critical. SentinelKarma provides the foundation for a new generation of collaborative security tools that empower network operators while protecting end users.

The system is designed for extensibility, with clear upgrade paths toward full decentralization, advanced analytics, and cross-chain interoperability. By open-sourcing the core technology and fostering a vibrant community, SentinelKarma aims to become the standard for decentralized network telemetry in Web3.

---

## Appendix A: Glossary

- **ASN**: Autonomous System Number, identifies network operators
- **Ed25519**: Elliptic curve signature algorithm used by Solana
- **JSONL**: JSON Lines, newline-delimited JSON format
- **KP**: Karma Points, non-transferable reputation metric
- **MQTT**: Message Queuing Telemetry Transport, pub/sub protocol
- **NFT**: Non-Fungible Token, unique digital asset
- **P95**: 95th percentile, statistical metric
- **PDA**: Program Derived Address, Solana account type
- **RPC**: Remote Procedure Call, API endpoint
- **SEKA**: SentinelKarma Token, fungible SPL token
- **SPL**: Solana Program Library, token standard
- **Z-Score**: Standard deviations from mean, anomaly metric

## Appendix B: References

1. Solana Documentation: https://docs.solana.com
2. Anchor Framework: https://www.anchor-lang.com
3. MQTT Specification: https://mqtt.org/mqtt-specification/
4. FastAPI Documentation: https://fastapi.tiangolo.com
5. Statistical Process Control: Montgomery, D.C. (2009)
6. Recharts Documentation: https://recharts.org

## Appendix C: Contact & Community

- **GitHub**: https://github.com/sentinelkarma
- **Documentation**: https://docs.sentinelkarma.io
- **Discord**: https://discord.gg/sentinelkarma
- **Twitter**: @sentinelkarma
- **Email**: team@sentinelkarma.io

---

**License**: MIT  
**Copyright**: 2025 SentinelKarma Contributors

*This whitepaper is a living document and will be updated as the project evolves.*
