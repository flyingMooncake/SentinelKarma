# Quick Start: Attack Blocking

Get started with automated attack blocking in 5 minutes.

---

## Prerequisites

- Linux system with root access (for iptables)
- Docker and Docker Compose
- SentinelKarma agent running
- MQTT broker accessible

---

## Step 1: Test the Classifier

First, verify the attack classifier works:

```bash
cd agent-python
python3 tools/attack_classifier.py
```

You should see test cases for different attack types.

---

## Step 2: Test the Blocker (Dry Run)

Test blocking without actually blocking:

```bash
# Set dry run mode
export DRY_RUN=true
export AUTO_BLOCK=true
export MIN_CONFIDENCE=0.7

# Run response daemon
python3 tools/response_daemon.py
```

In another terminal, generate some test traffic:

```bash
# Simulate attack via MQTT
mosquitto_pub -h localhost -t sentinel/diag -m '{
  "ts": 1234567890,
  "method": "getProgramAccounts",
  "metrics": {"calls": 5000, "err_rate": 0.05, "p95": 150},
  "z": {"lat": 2.0, "err": 1.5},
  "sample": "iphash:abc123"
}'
```

You should see:
```
[ALERT] DDOS detected
[ALERT] Severity: critical, Confidence: 90%
[DRY-RUN] Would execute: block_ips_immediately
```

---

## Step 3: Enable Real Blocking

⚠️ **Warning**: This will actually block IPs. Test in a safe environment first!

```bash
# Disable dry run
export DRY_RUN=false
export AUTO_BLOCK=true
export MIN_CONFIDENCE=0.8  # Higher threshold for safety

# Run with sudo (required for iptables)
sudo -E python3 tools/response_daemon.py
```

---

## Step 4: Monitor Blocked IPs

Check what's been blocked:

```bash
# View iptables rules
sudo iptables -L SENTINEL_BLOCK -n -v

# View blocklist file
cat /data/blocked_ips.txt

# View action log
tail -f /data/actions.log | jq
```

---

## Step 5: Manual Control

Manually block/unblock IPs:

```python
from tools.blocker import IPBlocker

blocker = IPBlocker()

# Block an IP
blocker.block_ip("192.168.1.100", reason="manual_block")

# List blocked IPs
print(blocker.list_blocked())

# Unblock an IP
blocker.unblock_ip("192.168.1.100")

# Get stats
print(blocker.get_stats())
```

---

## Step 6: Production Deployment

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  response-daemon:
    build: ./agent-python
    command: python3 tools/response_daemon.py
    environment:
      - MQTT_URL=mqtt://mosquitto:1883
      - AUTO_BLOCK=true
      - MIN_CONFIDENCE=0.8
      - DRY_RUN=false
      - ACTIONS_LOG=/data/actions.log
    volumes:
      - ./data:/data
    cap_add:
      - NET_ADMIN  # Required for iptables
    network_mode: host
    restart: unless-stopped
```

Start it:

```bash
docker-compose up -d response-daemon
docker-compose logs -f response-daemon
```

---

## Configuration Options

### Environment Variables

```bash
# Enable/disable automatic blocking
AUTO_BLOCK=true

# Minimum confidence to trigger auto-block (0.0-1.0)
MIN_CONFIDENCE=0.75

# Dry run mode (log only, don't actually block)
DRY_RUN=false

# Minimum requests to consider blocking
BLOCK_THRESHOLD=100

# MQTT broker URL
MQTT_URL=mqtt://mosquitto:1883

# Action log file
ACTIONS_LOG=/data/actions.log
```

---

## Safety Features

### 1. Confidence Threshold

Only high-confidence detections trigger auto-block:

```python
# In response_daemon.py
MIN_CONFIDENCE=0.8  # 80% confidence required
```

### 2. Dry Run Mode

Test without actually blocking:

```bash
DRY_RUN=true python3 tools/response_daemon.py
```

### 3. Manual Review

Disable auto-block for manual review:

```bash
AUTO_BLOCK=false python3 tools/response_daemon.py
```

### 4. Whitelist

Create a whitelist file:

```bash
# /data/whitelist.txt
10.0.0.1    # Internal network
192.168.1.1 # Gateway
```

Update blocker to check whitelist:

```python
# In blocker.py
def is_whitelisted(self, ip: str) -> bool:
    with open('/data/whitelist.txt', 'r') as f:
        for line in f:
            if line.strip().startswith(ip):
                return True
    return False

def block_ip(self, ip: str, reason: str = "malicious") -> bool:
    if self.is_whitelisted(ip):
        print(f"[BLOCKER] Skipping whitelisted IP: {ip}")
        return False
    # ... rest of blocking logic
```

---

## Troubleshooting

### "Permission denied" when running blocker

```bash
# Run with sudo
sudo python3 tools/response_daemon.py

# Or add user to sudoers for iptables
echo "username ALL=(ALL) NOPASSWD: /sbin/iptables" | sudo tee /etc/sudoers.d/sentinel
```

### Blocks not persisting after reboot

```bash
# Save iptables rules
sudo iptables-save > /etc/iptables/rules.v4

# Restore on boot (Ubuntu/Debian)
sudo apt install iptables-persistent
```

### Too many false positives

```bash
# Increase confidence threshold
MIN_CONFIDENCE=0.9

# Or disable auto-block
AUTO_BLOCK=false
```

### Need to unblock everything

```python
from tools.blocker import IPBlocker

blocker = IPBlocker()
blocker.clear_all()
```

---

## Monitoring

### Real-time logs

```bash
# Watch response daemon
tail -f /data/actions.log | jq

# Watch iptables
watch -n 1 'sudo iptables -L SENTINEL_BLOCK -n -v'
```

### Metrics

```bash
# Count blocked IPs
wc -l /data/blocked_ips.txt

# Count actions taken
wc -l /data/actions.log

# Recent attacks
tail -20 /data/actions.log | jq '.classification.type'
```

---

## Next Steps

1. **Integrate with nginx**: Generate nginx blocklists from SentinelKarma logs
2. **Share intelligence**: Upload validated blocks to IPFS for other peers
3. **Dashboard**: Build web UI to monitor and control blocking
4. **Alerting**: Send notifications to Slack/Discord/Email on critical attacks
5. **Machine Learning**: Train models on historical attack patterns

---

## Example: Complete Setup

```bash
#!/bin/bash
# setup-blocking.sh

# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Create data directory
mkdir -p /data

# 3. Create whitelist
cat > /data/whitelist.txt << EOF
127.0.0.1
10.0.0.0/8
192.168.0.0/16
EOF

# 4. Start in dry-run mode first
export DRY_RUN=true
export AUTO_BLOCK=true
export MIN_CONFIDENCE=0.8

echo "Starting in DRY-RUN mode..."
sudo -E python3 tools/response_daemon.py &

# 5. Monitor for 1 hour
sleep 3600

# 6. Review logs
echo "Reviewing actions taken..."
cat /data/actions.log | jq '.classification.type' | sort | uniq -c

# 7. If satisfied, enable real blocking
echo "Enable real blocking? (y/n)"
read answer
if [ "$answer" = "y" ]; then
    export DRY_RUN=false
    sudo -E python3 tools/response_daemon.py
fi
```

---

## Summary

✅ **Classifier** identifies attack types with confidence scores  
✅ **Blocker** uses iptables to drop malicious traffic  
✅ **Response Daemon** automates the detection → classification → blocking pipeline  
✅ **Safety features** prevent false positives (dry-run, confidence thresholds, whitelists)  
✅ **Monitoring** tracks all actions for audit and review  

**Result**: Attacks stopped in <1 second, fully automated, with safety controls.
