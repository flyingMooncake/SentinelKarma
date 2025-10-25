# SentinelKarma Manager - Command Reference

## 🚀 Quick Start

```bash
# First time setup
./manager.sh --install      # Install dependencies
./manager.sh --docker       # Setup Docker

# Start web dashboard
./manager.sh --web          # Production mode
./manager.sh --web --monitor-all  # With demo data
```

## 📋 Command Reference

### Setup & Installation

| Command | Description |
|---------|-------------|
| `--check` | Check if dependencies are installed |
| `--install` | Install all tools (Node.js, Docker, etc.) |
| `--docker` | Install Docker + build all images |
| `--update` | Update app and rebuild images |

### Main Commands

| Command | Description |
|---------|-------------|
| `--web` | Launch web dashboard (http://localhost:3000) |
| `--monitor` | Start monitoring services |
| `--test` | Test mode with multiple terminals |
| `--stop` | Stop all services |

### Modifier Flags

Use these with `--monitor` or `--web`:

| Flag | Description |
|------|-------------|
| `--monitor-all` | Include traffic generator (demo data) |
| `--full` | Enable auto-mint/upload processor |
| `--verbose` | Show all telemetry (not just attacks) |
| `--mute` | Run in background/detached mode |

## 🎯 Common Usage Patterns

### Production Monitoring
```bash
./manager.sh --monitor              # Real traffic only
./manager.sh --monitor --full       # + Auto-mint NFTs
```

### Testing/Development
```bash
./manager.sh --web --monitor-all    # Dashboard with demo data
./manager.sh --monitor --monitor-all --verbose  # See all data
```

### Background Operations
```bash
./manager.sh --web --mute           # Dashboard in background
./manager.sh --monitor --full --mute  # Full monitoring detached
```

## 🔧 Service Management

| Command | Description |
|---------|-------------|
| `--start` | Start only mosquitto broker |
| `--overburst` | Run stress test with malicious traffic |
| `--docker-purge` | Remove all containers/images |
| `--docker-reinstall` | Complete Docker reinstall (DESTRUCTIVE!) |

## ⛓️ Blockchain

| Command | Description |
|---------|-------------|
| `--solana` | Start local Solana testnet |
| `--solana --stop` | Stop Solana testnet |
| `--solana --silent` | Start Solana in background |

## 📊 Services Overview

| Service | Port | Description |
|---------|------|-------------|
| **web** | 3000 | React dashboard UI |
| **log-server** | 9000 | HTTP API server |
| **mosquitto** | 1883 | MQTT message broker |
| **agent** | - | Threat detection engine |
| **generator** | - | Traffic simulator |
| **saver** | - | Data persistence |

## 📁 Data Directories

| Directory | Purpose |
|-----------|---------|
| `data/contract_data/` | Logs for NFT minting |
| `data/malicious_logs/` | Detected attacks |
| `data/logs_normal/` | Normal traffic |
| `data/logs/` | Uploaded log files |

## 🔍 Detection Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `ERR_THR` | 0.05 | Error rate ≥ 5% = malicious |
| `ZLAT_THR` | 4 | Latency Z-score ≥ 4σ = malicious |
| `ZERR_THR` | 2 | Error Z-score ≥ 2σ = malicious |
| `P95_THR` | 250 | P95 latency ≥ 250ms = malicious |

## 💡 Examples

### Complete Setup
```bash
./manager.sh --check
./manager.sh --install
./manager.sh --docker
./manager.sh --web
```

### Daily Operations
```bash
# Start monitoring
./manager.sh --monitor

# Check status
docker compose ps

# View logs
docker compose logs -f agent

# Stop everything
./manager.sh --stop
```

### Testing
```bash
# With test traffic
./manager.sh --web --monitor-all

# Stress test
./manager.sh --overburst

# Full test mode
./manager.sh --test
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Permission denied | Add user to docker group: `sudo usermod -aG docker $USER` |
| Port in use | Check with `docker compose ps`, stop conflicting service |
| No data | Ensure generator is running (use `--monitor-all`) |
| Can't connect | Check if running: `curl http://localhost:9000/health` |

## 🌐 Access Points

- **Web Dashboard**: http://localhost:3000
- **API Server**: http://localhost:9000
- **Health Check**: http://localhost:9000/health
- **Statistics**: http://localhost:9000/stats

## 📚 More Information

- [Full Documentation](README.md)
- [Web Developer Guide](docs/WEB_DEVELOPER_GUIDE.md)
- [API Documentation](scripts/API_README.md)
- [Deployment Guide](docs/DEPLOYMENT.md)