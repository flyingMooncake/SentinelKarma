# Peer Log Server

Simple HTTP server for sharing malicious logs in the SentinelKarma network.

## Quick Start

### 1. Setup

```bash
cd infra/log-server

# Create data directory
mkdir -p data/logs

# Create authorized peers list (sync from blockchain)
cat > data/authorized_peers.txt << EOF
# Add authorized peer public keys (one per line)
ABC123...peer1_pubkey
DEF456...peer2_pubkey
EOF

# Set your public URL
export MY_PEER_URL=https://my-peer.sentinelkarma.io:9000
```

### 2. Run with Docker

```bash
docker-compose up -d
```

### 3. Check Health

```bash
curl http://localhost:9000/health
```

## Usage

### Upload Log (from your own peer)

```python
from client import LogClient
from solders.keypair import Keypair

# Load keypair
keypair = Keypair.from_base58_string("your_private_key")

# Initialize client
client = LogClient(keypair, my_server_url="http://localhost:9000")

# Upload log
log_url, file_hash = client.upload_log("/data/malicious_logs/attack.log")

print(f"Log URL: {log_url}")
print(f"Hash: {file_hash}")

# Submit to blockchain
await submit_nft_report(log_url=log_url, file_hash=file_hash)
```

### Download Log (from another peer)

```python
# Read from blockchain
post = await get_post(post_id)

# Download and verify
content = client.download_log(post.log_url, post.file_hash)

# Parse and use
attackers = parse_log(content)
for attacker in attackers:
    block_ip(attacker['ip'])
```

## Configuration

### Environment Variables

```bash
# Server settings
SERVER_HOST=0.0.0.0
SERVER_PORT=9000

# Storage
LOGS_DIR=/data/logs
MAX_LOG_SIZE=10485760      # 10MB per log
MAX_STORAGE=1073741824     # 1GB total

# Network
MY_PEER_URL=https://my-peer.com:9000
AUTHORIZED_PEERS_FILE=/data/authorized_peers.txt
```

## Deployment Options

### Option 1: Home Connection + Dynamic DNS

```bash
# Use DuckDNS for dynamic DNS
curl "https://www.duckdns.org/update?domains=mypeer&token=xxx&ip="

# Set URL
export MY_PEER_URL=https://mypeer.duckdns.org:9000

# Port forward 9000 on your router
```

### Option 2: Cloudflare Tunnel (No Port Forwarding)

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Create tunnel
./cloudflared tunnel --url http://localhost:9000

# You get: https://random-name.trycloudflare.com
export MY_PEER_URL=https://random-name.trycloudflare.com
```

### Option 3: VPS

```bash
# Just use your public IP/domain
export MY_PEER_URL=https://peer.sentinelkarma.io:9000

# Run with docker-compose
docker-compose up -d
```

## API Reference

### POST /logs

Upload a log file.

**Headers:**
- `X-Peer-Pubkey`: Your Solana public key
- `X-Timestamp`: Current Unix timestamp
- `X-Signature`: sign(filename + timestamp + pubkey)

**Body:**
- `file`: Log file (multipart/form-data)

**Response:**
```json
{
  "log_id": "abc123...",
  "url": "https://my-peer.com:9000/logs/abc123",
  "hash": "sha256_hash",
  "size": 12345
}
```

### GET /logs/{log_id}

Download a log file.

**Headers:**
- `X-Peer-Pubkey`: Your Solana public key
- `X-Timestamp`: Current Unix timestamp
- `X-Signature`: sign(log_id + timestamp + pubkey)

**Response:**
- Binary log file content

### GET /logs/{log_id}/metadata

Get log metadata (no auth required).

**Response:**
```json
{
  "log_id": "abc123",
  "filename": "attack.log",
  "uploader": "peer_pubkey",
  "timestamp": 1234567890,
  "hash": "sha256_hash",
  "size": 12345
}
```

### GET /health

Health check.

**Response:**
```json
{
  "status": "healthy",
  "logs_stored": 42,
  "storage_used_mb": 123.45,
  "storage_limit_mb": 1024.0,
  "authorized_peers": 10,
  "my_url": "https://my-peer.com:9000"
}
```

### GET /stats

Server statistics.

**Response:**
```json
{
  "total_logs": 42,
  "total_size_bytes": 123456789,
  "total_size_mb": 117.74,
  "storage_limit_mb": 1024.0,
  "authorized_peers": 10,
  "bandwidth_usage": {
    "ABC123...": 12345678
  }
}
```

## Security

### Rate Limiting

- 100MB per day per peer
- Automatic cleanup when storage limit reached
- 5-minute timestamp window for replay protection

### Access Control

- Only authorized peers can upload/download
- Signature verification on every request
- Peer list synced from blockchain

### Storage Management

- Automatic cleanup of old logs
- Configurable storage limits
- Per-log size limits

## Monitoring

### Logs

```bash
# View server logs
docker logs -f sentinel-log-server

# View access logs
tail -f data/logs/access.log
```

### Metrics

```bash
# Check stats
curl http://localhost:9000/stats | jq

# Check health
curl http://localhost:9000/health | jq
```

## Troubleshooting

### Port not accessible

```bash
# Check if server is running
docker ps | grep log-server

# Check firewall
sudo ufw allow 9000

# Test locally
curl http://localhost:9000/health
```

### Upload fails

```bash
# Check storage space
df -h

# Check logs
docker logs sentinel-log-server

# Verify authorized peers
cat data/authorized_peers.txt
```

### Download fails

```bash
# Check if peer is authorized
grep "peer_pubkey" data/authorized_peers.txt

# Check signature
# Verify timestamp is recent (within 5 minutes)

# Check bandwidth limit
curl http://localhost:9000/stats | jq '.bandwidth_usage'
```

## Cost

### Home Connection
- **Cost**: $0 (use existing internet)
- **Bandwidth**: Usually sufficient
- **Uptime**: Depends on your setup

### VPS
- **Cost**: $5/month (small VPS)
- **Bandwidth**: 1TB/month included
- **Uptime**: 99.9%

### Cloudflare Tunnel
- **Cost**: $0 (free tier)
- **Bandwidth**: Unlimited
- **Uptime**: Depends on your local machine

## Integration with Saver

Update `saver.py` to upload logs on rotation:

```python
from infra.log_server.client import LogClient

# Initialize client
keypair = Keypair.from_base58_string(os.getenv("PEER_PRIVATE_KEY"))
log_client = LogClient(keypair)

async def on_log_rotation(old_file_path: str):
    """Called when malicious log rotates"""
    # Upload to own server
    log_url, file_hash = log_client.upload_log(old_file_path)
    
    print(f"Uploaded: {log_url}, hash: {file_hash}")
    
    # Submit to blockchain
    await submit_to_contract(
        log_url=log_url,
        file_hash=file_hash,
        timestamp=int(time.time())
    )
    
    # Clean up local file
    os.remove(old_file_path)
```
