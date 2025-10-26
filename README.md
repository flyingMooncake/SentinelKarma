# 🛡️ SentinelKarma

**Decentralized Threat Intelligence Network for Solana**

SentinelKarma is a distributed security monitoring system that detects and mitigates attacks on Solana RPC infrastructure in real-time. The system combines statistical anomaly detection, peer-to-peer log sharing, and blockchain-based reputation to create a self-sustaining threat intelligence network.

---

## 🚀 Quick Start

```bash
# Install dependencies
./manager.sh --install

# Setup Docker
./manager.sh --docker

# Start Solana testnet
./manager.sh --solana

# Launch web dashboard
./manager.sh --web
```

**Web Dashboard**: http://localhost:3000  
**API Server**: http://localhost:9000  
**Solana RPC**: http://localhost:8899

---

## ✨ Features

- **Real-time Threat Detection** - Statistical anomaly detection on RPC traffic
- **Automated Log Classification** - Separates normal vs malicious traffic patterns
- **NFT-Based Reporting** - Immutable on-chain threat records
- **P2P Log Sharing** - Direct peer-to-peer HTTP log distribution
- **Karma Rewards** - Token incentives for accurate threat reporting
- **Web Dashboard** - Professional security monitoring interface
- **Auto-Mint System** - Automatic NFT minting for detected attacks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Web Dashboard (React + TypeScript)          │
│                    localhost:3000                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                  Log Server (FastAPI)                    │
│              HTTP API + P2P Log Sharing                  │
│                    localhost:9000                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────���────────┐
│                  MQTT Broker (Mosquitto)                 │
│              Real-time Message Distribution              │
│                    localhost:1883                        │
└─────┬──────────────┴──────────────┬────────────────────┘
      │                             │
┌─────┴─────┐                 ┌─────┴─────┐
│   Agent   │                 │   Saver   │
│ (Monitor) │                 │  (Logs)   │
└───────────┘                 └───────────┘
                                     │
                              ┌──────┴──────┐
                              │             │
                         Normal Logs   Malicious Logs
                         (30 min)      (30 sec rotation)
                                           │
                                    ┌──────┴──────┐
                                    │  Auto-Mint  │
                                    │  NFT Sync   │
                                    └──────┬──────┘
                                           │
                              ┌────────────┴────────────┐
                              │  Solana Blockchain      │
                              │  Sentinel Contract      │
                              └─────────────────────────┘
```

---

## 📦 Components

| Component | Description | Port |
|-----------|-------------|------|
| **Web Dashboard** | React security monitoring UI | 3000 |
| **Log Server** | FastAPI HTTP server for P2P log sharing | 9000 |
| **MQTT Broker** | Mosquitto message queue | 1883 |
| **Agent** | Python threat detection engine | - |
| **Saver** | Log classification and storage | - |
| **Generator** | Traffic simulator for testing | - |
| **NFT Sync** | Blockchain NFT synchronization daemon | - |
| **Solana Testnet** | Local validator for development | 8899 |

---

## 🛠️ Installation

### Prerequisites

- **OS**: Ubuntu/Debian Linux (or WSL2)
- **RAM**: 4GB minimum
- **Disk**: 20GB free space
- **Network**: Internet connection

### Full Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/SentinelKarma.git
cd SentinelKarma

# 2. Initialize submodules (Solana testnet)
git submodule update --init --recursive

# 3. Install dependencies
./manager.sh --install

# 4. Setup Docker and build images
./manager.sh --docker

# 5. Start Solana testnet
./manager.sh --solana --silent

# 6. Deploy smart contract
cd sentinel && ./deploy.sh && cd ..

# 7. Start web dashboard
./manager.sh --web
```

---

## 📊 Usage

### Web Dashboard

```bash
# Production mode (real traffic monitoring)
./manager.sh --web

# Demo mode (with simulated traffic)
./manager.sh --web --monitor-all

# Background mode
./manager.sh --web --mute
```

### Monitoring

```bash
# Start monitoring with web dashboard
./manager.sh --monitor --web

# With traffic generator for testing
./manager.sh --monitor --monitor-all

# Full auto-mint mode (processes and mints NFTs)
./manager.sh --monitor --full
```

### Solana Testnet

```bash
# Start validator
./manager.sh --solana

# Start in background
./manager.sh --solana --silent

# Stop validator
./manager.sh --solana --stop
```

### Testing

```bash
# Run stress test (overburst attack simulation)
./manager.sh --overburst

# Test mode with multiple terminals
./manager.sh --test
```

---

## 🔧 Manager Commands

| Command | Description |
|---------|-------------|
| `--help` | Show all available commands |
| `--check` | Check for missing dependencies |
| `--install` | Install system dependencies |
| `--docker` | Setup Docker and build images |
| `--solana` | Start Solana test validator |
| `--web` | Launch web dashboard |
| `--monitor` | Start monitoring services |
| `--full` | Enable full auto-mint mode |
| `--update` | Update and rebuild everything |
| `--stop` | Stop all services |
| `--overburst` | Run attack simulation |

### Command Combinations

```bash
# Start everything for development
./manager.sh --solana --silent && ./manager.sh --monitor --web --monitor-all

# Production monitoring
./manager.sh --monitor --web --full

# Testing and debugging
./manager.sh --test
```

---

## 🌐 Network Configuration

### Default Ports

- **Web Dashboard**: `3000`
- **API Server**: `9000`
- **MQTT Broker**: `1883`
- **Solana RPC**: `8899`
- **Solana WebSocket**: `8900`

### Environment Variables

```bash
# Detection Thresholds
ERR_THR=0.05        # Error rate threshold (5%)
ZLAT_THR=4          # Latency Z-score threshold
ZERR_THR=2          # Error Z-score threshold
P95_THR=250         # P95 latency threshold (ms)

# Time Windows
MAL_WINDOW_MIN=3    # Malicious log rotation (minutes)
NOR_WINDOW_MIN=30   # Normal log rotation (minutes)

# Log Server
SERVER_HOST=0.0.0.0
SERVER_PORT=9000
MAX_LOG_SIZE=10485760   # 10MB per log
MAX_STORAGE=1073741824  # 1GB total storage

# Auto-Mint Configuration
CHECK_INTERVAL=30       # Check for new logs every 30s
FILE_AGE_MINUTES=60     # Process files older than 60 min
```

---

## 🔐 Smart Contract

### Deployment

```bash
cd sentinel
./deploy.sh
```

The script will:
1. Start Solana testnet (if not running)
2. Build the contract
3. Deploy to local validator
4. Initialize the program
5. Save configuration

### Program Information

- **Program ID**: `Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V`
- **Network**: Local Testnet (devnet/mainnet ready)
- **Framework**: Anchor 0.28+

### Key Instructions

```rust
initialize()              // Deploy contract, mint initial SEKA
join_network()           // Pay 1000 SEKA to join
mint_nft(hash, db_addr)  // Submit threat report as NFT
like_nft(post)           // Validate report, earn karma
finalize_cycle()         // Distribute SEKA rewards
reset_karma()            // Reset karma for new cycle
```

---

## 🚀 Development

### Web Development

```bash
cd app
npm install
npm run dev  # Development server at localhost:5173
npm run build  # Production build
```

### Smart Contract Development

```bash
cd sentinel
anchor build
anchor test --skip-local-validator
```

### Python Development

```bash
cd agent-python
pip install -r requirements.txt
python -m tools.monitor  # Test monitoring
```

---

## 📚 Documentation

- **[WHITEPAPER.md](WHITEPAPER.md)** - Complete technical architecture
- **[sentinel/README.md](sentinel/README.md)** - Smart contract documentation
- **[sentinel/DEPLOY_LOCAL.md](sentinel/DEPLOY_LOCAL.md)** - Deployment guide

---

## 🔌 API Reference

### Log Server API

```http
# Upload log
POST /logs
Headers:
  X-Peer-Pubkey: <base58_pubkey>
  X-Timestamp: <unix_timestamp>
  X-Signature: <ed25519_signature>
Body: multipart/form-data with log file

# Download log (requires signature)
GET /logs/{log_id}
Headers:
  X-Peer-Pubkey: <base58_pubkey>
  X-Timestamp: <unix_timestamp>
  X-Signature: <ed25519_signature>

# Get log metadata
GET /logs/{log_id}/metadata

# Health check
GET /health

# Server statistics
GET /stats
```

### MQTT Topics

```
sentinel/diag              # All diagnostic messages
sentinel/region/{region}   # Regional filtering
sentinel/asn/{asn}         # ASN-specific alerts
sentinel/method/{method}   # Method-specific monitoring
```

---

## 🎯 Use Cases

### 1. RPC Provider Protection

Monitor your Solana RPC endpoint for abuse:
- Detect high error rates and heavy method abuse
- Receive real-time alerts via MQTT
- Automatically classify and store malicious logs
- Share threat intelligence with network peers

### 2. Collaborative Threat Intelligence

Join a network of RPC providers:
- Submit threat reports as NFTs
- Validate others' reports to earn karma
- Convert karma to SEKA tokens
- Access shared threat intelligence

### 3. Security Research

Analyze attack patterns:
- Collect real-world attack data
- Study RPC abuse techniques
- Develop mitigation strategies
- Contribute to Web3 security

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---


## 🔗 Links

- **GitHub**: https://github.com/sentinelkarma
- **Documentation**: [WHITEPAPER.md](WHITEPAPER.md)
- **Smart Contract**: [sentinel/README.md](sentinel/README.md)

---

## ⚡ Quick Reference

```bash
# First time setup
./manager.sh --install && ./manager.sh --docker

# Start Solana testnet
./manager.sh --solana --silent

# Deploy contract
cd sentinel && ./deploy.sh && cd ..

# Start everything
./manager.sh --monitor --web --monitor-all

# Stop everything
./manager.sh --stop && ./manager.sh --solana --stop
```

---

**Built with ❤️ for the Solana ecosystem**

**Status**: 🟢 ALFA Ready
**NEXT**: GOING FOR LIVE BABY ❤️❤️