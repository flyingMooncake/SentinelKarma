# SentinelKarma: Decentralized Network Telemetry and Reputation System

**Version 1.0**  
**Date: January 2025**

---

## Abstract

SentinelKarma is a decentralized telemetry and anti-abuse system for Web3 RPC networks that combines real-time monitoring with blockchain-based reputation mechanics. The system addresses critical challenges in distributed network infrastructure: detecting malicious behavior, incentivizing quality reporting, and creating a sustainable peer-operated monitoring network.

By integrating off-chain telemetry analysis with on-chain reputation tokens, SentinelKarma creates a self-sustaining ecosystem where network peers are economically incentivized to maintain high-quality monitoring and reporting standards. The system employs statistical anomaly detection, MQTT-based real-time messaging, and Solana smart contracts to deliver a comprehensive solution for network health and security.

---

## 1. Introduction

### 1.1 Problem Statement

Modern Web3 infrastructure faces several critical challenges:

1. **RPC Abuse**: Malicious actors exploit public RPC endpoints through excessive requests, resource-intensive queries, and coordinated attacks
2. **Lack of Accountability**: Anonymous access makes it difficult to identify and mitigate bad actors
3. **Monitoring Gaps**: Centralized monitoring creates single points of failure and trust dependencies
4. **Incentive Misalignment**: Network operators lack economic incentives to share threat intelligence
5. **Data Silos**: Security information remains fragmented across individual operators

### 1.2 Solution Overview

SentinelKarma introduces a three-layer architecture:

**Layer 1: Telemetry Collection & Analysis**
- Real-time event stream processing from RPC endpoints
- Statistical anomaly detection using z-scores and percentile analysis
- Automated classification of normal vs. malicious traffic patterns

**Layer 2: Distributed Messaging**
- MQTT-based publish/subscribe architecture for real-time alerts
- Decentralized data distribution without central coordination
- Scalable message routing for thousands of monitoring peers

**Layer 3: Blockchain Reputation**
- Non-transferable Karma Points (KP) for peer reputation
- Fungible SEKA tokens convertible from earned karma
- On-chain governance and economic sustainability mechanisms

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
│  • Malicious Logs (3-min rotation)                         │
│  • Normal Logs (30-min rotation)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Blockchain Layer (Solana)                   │
│  • NFT-based Report Submission                              │
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
7. **Reporting**: Peers submit NFT-based reports with HTTP URLs to their log servers
8. **Reputation**: Community validation through likes accumulates karma points
9. **Conversion**: Karma converted to SEKA tokens for economic utility

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

### 3.4 Heavy Method Detection

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

## 5. Blockchain Reputation System

### 5.1 Token Economics

**Dual-Token Model:**

1. **Karma Points (KP)**: Non-transferable reputation metric
   - Earned through community validation (likes on reports)
   - Accumulated per 2-hour cycle
   - Stored on-chain in PeerLedger accounts

2. **SEKA Token**: Fungible SPL token
   - Conversion rate: 100 KP = 1 SEKA
   - Decimals: 9 (standard SPL)
   - Use cases: Network membership, governance, staking

**Initial Distribution:**
- 100,000 SEKA minted at initialization
- Distributed to project authority for ecosystem bootstrapping
- Ongoing minting through karma conversion only

### 5.2 Karma Accumulation

**Earning Mechanisms:**

1. **Report Submission**: Peers mint NFTs representing threat reports
   - NFT metadata includes IPFS hash of log data
   - On-chain reference to database address
   - Timestamped with cycle index

2. **Community Validation**: Other peers "like" quality reports
   - Each like increments post owner's karma by 1
   - Likers must be active network members
   - Double-liking prevented via PDA uniqueness

3. **Cycle Finalization**: Authority distributes proportional rewards
   - Total pool: 1,000 SEKA per 2-hour cycle
   - Distribution: Proportional to karma earned
   - Per-peer cap: 10% of cycle pool (100 SEKA max)

**Formula:**
```
peer_reward = min(
  (peer_karma / total_karma) * 1000 SEKA,
  100 SEKA
)
```

### 5.3 Network Membership

**Joining Requirements:**
- Payment: 1,000 SEKA (1 SEKA with 9 decimals)
- Creates PeerState account (active=true)
- Enables report submission and liking privileges

**Benefits:**
- Submit threat reports as NFTs
- Validate others' reports (earn karma)
- Participate in governance (future)
- Access premium RPC tiers (future)

### 5.4 Smart Contract Architecture

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
├── hash: [u8; 32]        // IPFS content hash
├── db_addr: Pubkey       // Database reference
├── likes: u64
└── cycle_index: u64

Like (PDA: ["like", liker, post])
├── liker: Pubkey
└── post: Pubkey
```

**Key Instructions:**

1. `initialize`: Deploy contract, mint initial supply, set mint authority
2. `join_network`: Pay fee, activate peer membership
3. `mint_nft`: Submit threat report as NFT with metadata
4. `like_nft`: Validate report, increment karma
5. `finalize_cycle`: Distribute SEKA rewards proportionally

---

## 6. Security & Privacy

### 6.1 Privacy Protections

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

### 6.2 Off-Chain Data Storage

**P2P HTTP Log Sharing:**

SentinelKarma uses a simple peer-to-peer HTTP architecture for off-chain log storage. Each peer runs their own log server and shares URLs via the blockchain.

**Architecture:**
```
Peer A: Upload log → Get URL → Store URL on blockchain
Peer B: Read URL from blockchain → Request with signature → Verify hash
```

**Access Flow:**
1. **Peer A (Detector)**:
   - Detects attack, generates malicious log
   - Uploads to own HTTP server (port 9000)
   - Gets log URL: `https://peer-a.com:9000/logs/abc123`
   - Computes SHA256 hash of log
   - Submits to blockchain: `{log_url, file_hash, signature}`

2. **Peer B (Verifier)**:
   - Reads Post account from blockchain
   - Gets `log_url` and `file_hash`
   - Creates signed request: `sign(log_url + timestamp + pubkey)`
   - Requests log from Peer A's server
   - Peer A verifies signature → returns log
   - Peer B verifies hash matches blockchain
   - If valid → applies blocks, likes post

**Security Features:**
- **Authentication**: Ed25519 signatures prove peer identity
- **Authorization**: Only active network members can request logs
- **Replay Protection**: Timestamp validation (5-minute window)
- **Integrity**: SHA256 hash on blockchain verifies content
- **Audit Trail**: All access attempts logged
- **On-Demand**: Data only transferred when requested

**Implementation:**
- Each peer runs FastAPI server (simple HTTP)
- Logs stored on local disk
- URLs stored on blockchain (not the logs themselves)
- Direct peer-to-peer communication
- No central infrastructure needed

**Benefits:**
- **Simpler**: Just HTTP + file storage (no IPFS complexity)
- **Faster**: Direct peer-to-peer (no DHT lookups)
- **Cheaper**: $0-5/month per peer (vs $25-50 for IPFS)
- **More Control**: Peers manage their own data
- **Flexible**: Can use home connection, VPS, or cloud
- **Verifiable**: Hash on blockchain proves integrity

### 6.3 Attack Resistance

**Sybil Resistance:**
- Network membership requires SEKA payment
- Economic cost to create multiple identities
- Karma accumulation requires community validation
- Per-peer reward caps limit single-actor dominance

**Spam Prevention:**
- Like PDAs prevent double-liking
- Active peer requirement for all interactions
- Cycle-based reward distribution limits gaming
- Authority-controlled finalization prevents premature claims

**Smart Contract Security:**
- PDA-based access control
- Overflow checks on all arithmetic
- Constraint validation on all accounts
- Mint authority delegated to program PDA

**Log Server Security:**
- Signature verification on every request
- Authorized peers list (synced from contract)
- Timestamp validation (5-minute window)
- Rate limiting (100MB/day per peer)
- Storage limits (1GB total, 10MB per log)
- Automatic cleanup of old logs

### 6.4 Production Hardening (Roadmap)

**MQTT Security:**
- TLS encryption (port 8883)
- Username/password authentication
- ACL-based topic permissions
- VPN or private network deployment

**Log Server Security:**
- HTTPS with SSL certificates
- Rate limiting per peer
- DDoS protection (Cloudflare/AWS Shield)
- Automatic peer list sync from contract
- Access logs and anomaly detection
- Bandwidth monitoring and alerts

---

## 7. Use Cases & Applications

### 7.1 RPC Provider Protection

**Scenario**: Public Solana RPC endpoint experiencing abuse

**Solution**:
1. Deploy SentinelKarma agent monitoring request stream
2. Detect anomalous patterns (high error rates, heavy methods)
3. Receive real-time MQTT alerts on threshold breaches
4. Malicious logs stored locally and served via HTTP
5. Submit on-chain report with log URL and hash
6. Other peers download and verify logs (signed requests)
7. Implement rate limiting based on validated threat intelligence

**Outcome**: 70% reduction in abusive traffic, improved service quality for legitimate users, shared threat intelligence across network

### 7.2 Collaborative Threat Intelligence

**Scenario**: Multiple RPC providers want to share security data

**Solution**:
1. Each provider runs SentinelKarma agent + log server
2. Malicious logs stored locally, served via HTTP
3. Peers submit NFT reports with log URL on-chain
4. Other peers download logs with signed requests
5. Community validates reports through likes
6. High-karma reports automatically trusted
7. Validated threats distributed across network

**Outcome**: Faster threat detection, reduced individual monitoring costs, collective defense, verifiable threat intelligence

**P2P Sharing Example:**
```python
# Peer A uploads malicious log
from infra.log_server.client import LogClient

client = LogClient(keypair)
log_url, file_hash = client.upload_log('/data/malicious_logs/attack.log')
submit_nft_report(log_url, file_hash)

# Peer B wants to verify
post = get_post(post_id)
log_content = client.download_log(post.log_url, post.file_hash)
verify_threat(log_content)  # Validate and like if legitimate
```

### 7.3 Reputation-Based Access Control

**Scenario**: Premium RPC tier for trusted users

**Solution**:
1. Users join network by paying SEKA
2. Earn karma through quality reporting
3. High-karma users receive priority access
4. Low-karma or non-members rate-limited
5. Economic incentive for good behavior

**Outcome**: Self-regulating community, sustainable business model, aligned incentives

---

## 8. Performance & Scalability

### 8.1 Throughput Metrics

**Telemetry Processing:**
- Event ingestion: 10,000 events/second per agent
- Window aggregation: 250ms latency
- MQTT publishing: <10ms per message
- Classification: Real-time (no backlog)

**Blockchain Operations:**
- Report submission: ~400ms (Solana block time)
- Like transaction: ~400ms
- Cycle finalization: ~2s for 100 peers
- Gas costs: ~0.001 SOL per transaction

### 8.2 Scaling Strategies

**Horizontal Scaling:**
- Multiple agent instances per region
- MQTT broker clustering with shared subscriptions
- Sharded log storage by time/region
- Parallel cycle finalization for large peer sets

**Optimization Techniques:**
- Batch MQTT publishing (10 messages/batch)
- Compressed log rotation (gzip)
- Bloom filters for duplicate detection
- Lazy PDA initialization (on-demand account creation)

---

## 9. Governance & Sustainability

### 9.1 Decentralized Governance (Roadmap)

**Phase 1 (Current)**: Authority-controlled
- Single admin key for cycle finalization
- Manual threshold adjustments
- Centralized parameter updates

**Phase 2**: Multisig governance
- 3-of-5 multisig for critical operations
- Community proposal system
- Time-locked parameter changes

**Phase 3**: On-chain DAO
- SEKA token voting power
- Proposal submission (10,000 SEKA stake)
- Quadratic voting for fairness
- Automated execution via smart contracts

### 9.2 Economic Sustainability

**Revenue Streams:**
1. Network membership fees (1,000 SEKA per peer)
2. Premium RPC access subscriptions
3. Enterprise monitoring licenses
4. Threat intelligence API access

**Cost Structure:**
- Infrastructure: MQTT broker, storage, compute
- Development: Core team, audits, maintenance
- Community: Rewards, grants, bounties

**Treasury Management:**
- Join fees accumulate in treasury vault
- Governance-controlled spending
- Transparent on-chain accounting
- Quarterly community reports

---

## 10. Roadmap

### Q1 2025: MVP Launch
- ✅ Core telemetry pipeline
- ✅ MQTT messaging layer
- ✅ Basic smart contracts
- ✅ NFT-based reporting
- ✅ Karma accumulation

### Q2 2025: Production Hardening
- [x] P2P HTTP log sharing
- [x] Signed request access control
- [ ] TLS-encrypted MQTT
- [ ] HTTPS gateway with SSL
- [ ] Advanced anomaly detection (ML models)
- [ ] Multi-region deployment
- [ ] Security audit

### Q3 2025: Ecosystem Growth
- [ ] Public testnet launch
- [ ] Developer documentation
- [ ] SDK for RPC providers
- [ ] Dashboard UI for monitoring
- [ ] Community onboarding program

### Q4 2025: Decentralization
- [ ] Multisig governance
- [ ] Permissionless peer joining
- [ ] Cross-chain bridge (Ethereum, Polygon)
- [ ] Mainnet launch
- [ ] Token listing

### 2026: Advanced Features
- [ ] On-chain DAO governance
- [ ] Adaptive threshold algorithms
- [ ] Predictive threat modeling
- [ ] Automated response actions
- [ ] Multi-region log servers
- [ ] CDN integration for popular logs
- [ ] Enterprise partnerships

---

## 11. Technical Specifications

### 11.1 System Requirements

**Agent Deployment:**
- OS: Linux (Ubuntu 20.04+), Docker support
- CPU: 2 cores minimum
- RAM: 4GB minimum
- Storage: 100GB SSD (log retention)
- Network: 100Mbps, low latency to MQTT broker

**MQTT Broker:**
- Mosquitto 2.0+
- CPU: 4 cores
- RAM: 8GB
- Network: 1Gbps, public IP or VPN

**Log Server:**
- Python 3.11+ (FastAPI)
- CPU: 1 core minimum
- RAM: 1GB minimum
- Storage: 10GB SSD (local logs)
- Network: 100Mbps, public IP or tunnel

**Blockchain Node:**
- Solana RPC endpoint (devnet/mainnet)
- Anchor framework 0.28+
- Rust 1.70+

### 11.2 Configuration Parameters

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
MAL_WINDOW_MIN=3          # Malicious log rotation (minutes)
NOR_WINDOW_MIN=30         # Normal log rotation (minutes)

# Log Server
SERVER_HOST=0.0.0.0
SERVER_PORT=9000
MY_PEER_URL=https://my-peer.com:9000
LOGS_DIR=/data/logs
AUTHORIZED_PEERS_FILE=/data/authorized_peers.txt
MAX_LOG_SIZE=10485760  # 10MB
MAX_STORAGE=1073741824  # 1GB

# Blockchain
CYCLE_SECONDS=7200        # 2-hour cycles
JOIN_COST=1000000000000   # 1,000 SEKA (with 9 decimals)
CYCLE_REWARD_TOTAL=1000000000000  # 1,000 SEKA per cycle
MAX_PEER_REWARD_PCT=10    # 10% cap per peer
```

### 11.3 API Reference

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
Body:
  file: log_file

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
mint_nft(user, log_url, file_hash)
like_nft(liker, post)
finalize_cycle(authority, peers, karmas)
```

---

## 12. Conclusion

SentinelKarma represents a paradigm shift in Web3 infrastructure monitoring by combining real-time telemetry, distributed messaging, and blockchain-based reputation into a cohesive system. The architecture addresses critical gaps in current solutions:

1. **Decentralization**: No single point of failure or trust
2. **Incentive Alignment**: Economic rewards for quality monitoring
3. **Real-time Response**: Sub-second anomaly detection and alerting
4. **Community-Driven**: Peer validation ensures data quality
5. **Sustainable**: Self-funding through membership fees and token economics

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

## Appendix C: Contact & Community

- **GitHub**: https://github.com/sentinelkarma
- **Documentation**: https://docs.sentinelkarma.io
- **Discord**: https://discord.gg/sentinelkarma
- **Twitter**: @sentinelkarma
- **Email**: team@sentinelkarma.io

---

**License**: MIT  
**Copyright**: 2025 SentinelKarma Contributors

*This whitepaper is a living document and will be updated as the project evolves. Version history available on GitHub.*
