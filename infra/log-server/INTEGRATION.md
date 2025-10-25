# Log Server Integration

The HTTP log server is now integrated into the main SentinelKarma stack and launches automatically with the monitor.

## Quick Start

```bash
# Build all images including log-server
./manager.sh --docker

# Start monitoring with log server
./manager.sh --monitor

# The log server will be available at:
# http://localhost:9000
```

## Endpoints

### Health Check
```bash
curl http://localhost:9000/health
```

Returns:
```json
{
  "status": "healthy",
  "logs_stored": 0,
  "storage_used_mb": 0.0,
  "storage_limit_mb": 1024.0,
  "authorized_peers": 0,
  "my_url": "http://localhost:9000"
}
```

### Statistics
```bash
curl http://localhost:9000/stats
```

### Upload Log (requires authentication)
```bash
curl -X POST http://localhost:9000/logs \
  -H "X-Peer-Pubkey: YOUR_SOLANA_PUBKEY" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Signature: YOUR_SIGNATURE" \
  -F "file=@/path/to/log.jsonl"
```

### Download Log (requires authentication)
```bash
curl http://localhost:9000/logs/LOG_ID \
  -H "X-Peer-Pubkey: YOUR_SOLANA_PUBKEY" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Signature: YOUR_SIGNATURE" \
  -o downloaded_log.jsonl
```

## Configuration

Environment variables (set in docker-compose.yml):

- `SERVER_HOST`: Bind address (default: 0.0.0.0)
- `SERVER_PORT`: Port to listen on (default: 9000)
- `LOGS_DIR`: Directory for log storage (default: /data/logs)
- `AUTHORIZED_PEERS_FILE`: Path to authorized peers list (default: /data/authorized_peers.txt)
- `MY_PEER_URL`: Public URL of this peer (default: http://localhost:9000)
- `MAX_LOG_SIZE`: Maximum log file size in bytes (default: 10MB)
- `MAX_STORAGE`: Maximum total storage in bytes (default: 1GB)

## Authorized Peers

The server reads authorized peer public keys from `data/authorized_peers.txt`. This file should be synced from the blockchain PeerState accounts.

Format:
```
# Comments start with #
7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
AnotherPeerPublicKeyHere...
```

## Integration with Manager

The log server is automatically:
- Built when running `./manager.sh --docker`
- Started when running `./manager.sh --monitor`
- Stopped when running `./manager.sh --stop`
- Purged when running `./manager.sh --docker-purge`

## Data Persistence

Logs are stored in `./data/logs/` and persist across container restarts.

## Monitoring

View log server logs:
```bash
docker compose logs -f log-server
```

Check container status:
```bash
docker compose ps log-server
```

## Security Notes

**For Development:**
- Signature verification is simplified (TODO: implement proper Ed25519)
- No TLS encryption (use HTTP only)
- Authorized peers list must be manually maintained

**For Production:**
- Implement proper Ed25519 signature verification with solders
- Enable HTTPS with SSL certificates
- Sync authorized peers from blockchain automatically
- Add rate limiting per peer
- Enable DDoS protection
- Use private network or VPN

## Troubleshooting

**Server not starting:**
```bash
# Check logs
docker compose logs log-server

# Verify port is available
netstat -tuln | grep 9000
```

**Health check failing:**
```bash
# Test directly
curl -v http://localhost:9000/health

# Check container
docker compose exec log-server python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:9000/health').read())"
```

**Permission issues:**
```bash
# Fix data directory permissions
sudo chown -R $(id -u):$(id -g) data/logs
chmod 755 data/logs
```
