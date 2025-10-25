# SentinelKarma Python APIs

Complete Python API libraries for interacting with the SentinelKarma system.

## Installation

```bash
pip install requests
```

## Available APIs

### 1. SentinelKarmaAPI (Combined API)

Main API that combines all functionality:

```python
from sentinel_api import SentinelKarmaAPI

# Initialize (auto-detects IP address)
api = SentinelKarmaAPI()

# Get system status
status = api.status()
print(f"IP: {status['ip']}")
print(f"Log Server: {status['log_server']['url']}")
print(f"Balance: {status['contract']['balance']} SOL")

# Process a log file (upload + mint NFT)
result = api.process_log_file("data/contract_data/test.log")
```

### 2. LogServerAPI

HTTP log server interactions:

```python
from sentinel_api import LogServerAPI

# Initialize (auto-detects IP)
api = LogServerAPI()

# Check health
health = api.health()

# Upload a log
result = api.upload_log("path/to/file.log")
print(f"Log ID: {result['log_id']}")
print(f"URL: {result['url']}")

# Download a log
api.download_log("ed2336ded3a9213a", "output.log")

# Check if file exists
exists = api.check_exists(file_hash)

# List all logs
logs = api.list_logs()
for log in logs:
    print(f"{log['log_id']}: {log['filename']}")
```

### 3. SentinelContractAPI

Solana contract interactions:

```python
from sentinel_api import SentinelContractAPI

# Initialize (auto-detects RPC)
api = SentinelContractAPI()

# Check balance
balance = api.get_balance()
print(f"Balance: {balance} SOL")

# Request airdrop (testnet)
api.airdrop(100)

# Create NFT mint
mint_address = api.create_nft_mint()

# Mint NFT for log
result = api.mint_nft(
    log_url="http://172.19.12.161:9000/logs/abc123",
    file_hash="sha256_hash_here"
)
```

### 4. DockerManagerAPI

Control Docker services:

```python
from docker_api import DockerManagerAPI

# Initialize
docker = DockerManagerAPI()

# Start all services
docker.start_services()

# Start monitoring (full mode with auto-mint)
docker.monitor_start(full=True)

# Get service status
status = docker.get_service_status()
for service, state in status.items():
    print(f"{service}: {state}")

# Get logs from a service
logs = docker.get_logs("agent", lines=100)

# Restart a service
docker.restart_service("log-server")

# Health check all services
health = docker.health_check()

# Get statistics
stats = docker.get_stats()
```

## Auto-Detection Features

All APIs automatically detect your WSL IP address instead of using localhost:

```python
# Automatic IP detection
api = SentinelKarmaAPI()  # Uses detected IP

# Manual override if needed
api = LogServerAPI(server_url="http://192.168.1.100:9000")
```

## Complete Example

```python
from sentinel_api import SentinelKarmaAPI
from docker_api import DockerManagerAPI

# Start services
docker = DockerManagerAPI()
docker.start_services()

# Initialize API
api = SentinelKarmaAPI()

# Check system
status = api.status()
print(f"System IP: {status['ip']}")

# Process all contract data files
from pathlib import Path

log_dir = Path("data/contract_data")
for log_file in log_dir.glob("*.log"):
    # Check if already uploaded
    file_hash = api.log_server._compute_hash(str(log_file))
    if not api.log_server.check_exists(file_hash):
        # Upload and mint
        result = api.process_log_file(str(log_file))
        print(f"Processed: {log_file.name}")
        print(f"  Upload: {result['upload']}")
        print(f"  Mint: {result['mint']}")
```

## Monitoring Script

The auto-mint monitor now uses the detected IP:

```bash
# Run full monitoring (auto-processes new files)
./manager.sh --monitor --full

# Or run directly
python3 scripts/auto_mint_monitor.py
```

## API Methods Reference

### SentinelKarmaAPI

- `status()` - Get complete system status
- `process_log_file(filepath)` - Upload and mint NFT for a log

### LogServerAPI

- `health()` - Check server health
- `stats()` - Get server statistics
- `upload_log(filepath)` - Upload a log file
- `download_log(log_id, output_path)` - Download a log
- `get_metadata(log_id)` - Get log metadata
- `list_logs()` - List all available logs
- `check_exists(file_hash)` - Check if file exists

### SentinelContractAPI

- `get_balance(address)` - Get SOL balance
- `airdrop(amount, address)` - Request testnet airdrop
- `create_nft_mint()` - Create new NFT mint
- `mint_nft(log_url, file_hash)` - Mint NFT for log
- `get_peer_info(peer_address)` - Get peer information

### DockerManagerAPI

- `check_dependencies()` - Check if dependencies installed
- `install_dependencies()` - Install required tools
- `setup_docker()` - Setup Docker and build images
- `start_services(services)` - Start services
- `stop_services(services)` - Stop services
- `restart_service(service)` - Restart a service
- `get_service_status(service)` - Get service status
- `get_logs(service, lines)` - Get service logs
- `monitor_start(full, verbose, mute)` - Start monitoring
- `test_mode()` - Start test mode
- `overburst(methods, rate)` - Run overburst test
- `build_images()` - Rebuild Docker images
- `purge_project()` - Purge containers/images
- `exec_command(service, command)` - Execute command in container
- `health_check()` - Check health of all services
- `get_stats()` - Get statistics

## Environment Variables

```bash
# Override defaults
export LOG_SERVER_URL="http://192.168.1.100:9000"
export RPC_URL="http://192.168.1.100:8899"
export KEYPAIR_PATH="/path/to/keypair.json"
```

## Testing

Run the example scripts:

```bash
# Test API functionality
python3 scripts/example_api_usage.py

# Test Docker management
python3 scripts/docker_api.py

# Test main API
python3 scripts/sentinel_api.py
```

## Notes

- All APIs use auto-detected WSL IP by default (not localhost)
- Testing mode enabled (no signature verification)
- NFT minting is placeholder (contract deployment needed)
- Log server must be running (`./manager.sh --monitor`)
- Solana testnet must be running for contract operations