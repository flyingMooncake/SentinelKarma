# 🛡️ SentinelKarma

**Decentralized Threat Intelligence Network for Solana**

SentinelKarma is a distributed security system that detects and mitigates attacks on Solana RPC infrastructure in real-time, rewarding participants with karma tokens for accurate threat reporting.

## 🚀 Quick Start

```bash
# Install dependencies
./manager.sh --install

# Setup Docker
./manager.sh --docker

# Launch web dashboard
./manager.sh --web

# Or start with demo data
./manager.sh --web --monitor-all
```

**Dashboard**: http://localhost:3000  
**API Server**: http://localhost:9000

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Web Dashboard (React)                  │
└─────────────────────────────────────────────────────────┘
                            │
┌──────────────────────��──────────────────────────────────┐
│                    Monitoring Layer                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  │
│  │  Agent  │  │  Saver  │  │Generator│  │Log Server│  │
│  └─────────┘  └─────────┘  └─────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     MQTT Broker                          │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                  Solana Blockchain                       │
│              (Sentinel Smart Contract)                   │
└─────────────────────────────────────────────────────────┘
```

## ✨ Features

- **Real-time Threat Detection**: Monitors RPC traffic for attacks
- **Distributed Network**: Peer-to-peer threat intelligence sharing
- **Karma Rewards**: Token incentives for accurate reporting
- **NFT Logging**: Immutable on-chain threat records
- **Web Dashboard**: Professional security monitoring interface
- **Auto-mitigation**: Automatic blocking of malicious peers

## 📦 Components

| Component | Description | Port |
|-----------|-------------|------|
| **Web Dashboard** | React security monitoring UI | 3000 |
| **Log Server** | HTTP API for log storage | 9000 |
| **MQTT Broker** | Message queue for real-time data | 1883 |
| **Agent** | Threat detection engine | - |
| **Generator** | Traffic simulator for testing | - |
| **Saver** | Data persistence service | - |

## 🛠️ Installation

### Prerequisites

- Ubuntu/Debian Linux (or WSL2)
- 4GB+ RAM
- 10GB+ disk space

### Full Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/SentinelKarma.git
cd SentinelKarma

# 2. Install all dependencies
./manager.sh --install

# 3. Setup Docker and build images
./manager.sh --docker

# 4. Start services
./manager.sh --web
```

## 📊 Usage

### Web Dashboard

```bash
# Production mode (real traffic)
./manager.sh --web

# Demo mode (with simulated traffic)
./manager.sh --web --monitor-all

# Background mode
./manager.sh --web --mute
```

### Monitoring

```bash
# Start monitoring
./manager.sh --monitor

# With traffic generator
./manager.sh --monitor --monitor-all

# Full mode (auto-mint NFTs)
./manager.sh --monitor --full
```

### Testing

```bash
# Run stress test
./manager.sh --overburst

# Test mode with multiple terminals
./manager.sh --test
```

## 🔧 Management Commands

| Command | Description |
|---------|-------------|
| `--install` | Install all dependencies |
| `--docker` | Setup Docker and build images |
| `--web` | Launch web dashboard |
| `--monitor` | Start monitoring services |
| `--update` | Update and rebuild everything |
| `--stop` | Stop all services |
| `--help` | Show all commands |

## 📚 Documentation

- [Web Developer Guide](docs/WEB_DEVELOPER_GUIDE.md) - Extend the web dashboard
- [Manager Help](MANAGER_HELP.md) - Complete command reference
- [API Documentation](scripts/API_README.md) - Python/TypeScript APIs
- [Whitepaper](WHITEPAPER.md) - Technical architecture
- [Contract Deployment](sentinel/README.md) - Deploy smart contract

## 🔌 APIs

### Python

```python
from scripts.sentinel_api import SentinelKarmaAPI

api = SentinelKarmaAPI()
status = api.status()
result = api.process_log_file("data/test.log")
```

### TypeScript

```typescript
import { SentinelKarmaAPI } from './scripts/sentinel-api';

const api = new SentinelKarmaAPI();
const status = await api.status();
```

## 🌐 Network Configuration

### Default Ports

- Web Dashboard: `3000`
- API Server: `9000`
- MQTT Broker: `1883`
- Solana RPC: `8899`

### Environment Variables

```bash
# Detection thresholds
ERR_THR=0.05        # Error rate threshold
ZLAT_THR=4          # Latency Z-score threshold
P95_THR=250         # P95 latency threshold

# Time windows
MAL_WINDOW_MIN=3    # Malicious log rotation
NOR_WINDOW_MIN=30   # Normal log rotation
```

## 🚀 Development

### Web Development

```bash
cd app
npm install
npm run dev  # Hot reload at localhost:5173
```

See [Web Developer Guide](docs/WEB_DEVELOPER_GUIDE.md) for details.

### Smart Contract

```bash
cd sentinel
anchor build
anchor test
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](docs/)
- [Web Dashboard Guide](docs/WEB_DEVELOPER_GUIDE.md)
- [API Reference](scripts/API_README.md)
- [Whitepaper](WHITEPAPER.md)

## ⚡ Quick Commands

```bash
# First time setup
./manager.sh --install && ./manager.sh --docker

# Start everything
./manager.sh --web --monitor-all

# Update to latest
./manager.sh --update

# Stop everything
./manager.sh --stop
```

---

**Built with ❤️ for the Solana ecosystem**