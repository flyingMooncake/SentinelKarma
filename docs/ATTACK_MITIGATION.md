# Attack Mitigation Guide

How to use SentinelKarma logs to detect and stop attacks in real-time.

---

## Overview

SentinelKarma provides multiple layers of defense:

1. **Real-time Detection**: Identify attacks as they happen (250ms windows)
2. **Automated Response**: Block malicious IPs immediately
3. **Shared Intelligence**: Learn from other peers' detections
4. **Adaptive Defense**: Update rules based on validated threats

---

## Attack Response Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Agent detects anomaly (high error rate, latency spike)  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Classify attack type:                                    │
│     - DDoS (volume)                                          │
│     - Resource exhaustion (heavy methods)                    │
│     - Scanning/fuzzing (high error rate)                     │
│     - Credential stuffing (repeated failures)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Extract attacker IPs from logs                           │
│     - Parse malicious log window                             │
│     - Identify top offenders by request count                │
│     - Calculate attack severity score                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────���──────────────────────────────────────────┐
│  4. Apply mitigation:                                        │
│     - Add to firewall blocklist (iptables/nftables)         │
│     - Rate limit at nginx/haproxy                            │
│     - Update WAF rules                                       │
│     - Notify security team                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Share with network:                                      │
│     - Upload log to IPFS                                     │
│     - Submit on-chain report                                 │
│     - Other peers download and apply same blocks             │
└────��────────────────────────────────────────────────────────┘
```

---

## 1. Real-Time Blocking

### Automatic IP Blocking

When agent detects malicious activity, automatically block the source IPs:

```python
# agent-python/tools/blocker.py
import subprocess
import os
from typing import List, Set

class IPBlocker:
    """Automatically block malicious IPs using iptables"""
    
    def __init__(self):
        self.blocked_ips: Set[str] = set()
        self.blocklist_file = "/etc/sentinel/blocked_ips.txt"
        self.load_existing_blocks()
    
    def load_existing_blocks(self):
        """Load previously blocked IPs"""
        if os.path.exists(self.blocklist_file):
            with open(self.blocklist_file, 'r') as f:
                self.blocked_ips = set(line.strip() for line in f)
    
    def block_ip(self, ip: str, reason: str = "malicious"):
        """Block an IP using iptables"""
        if ip in self.blocked_ips:
            return  # Already blocked
        
        try:
            # Add to iptables
            subprocess.run([
                'iptables', '-A', 'INPUT',
                '-s', ip,
                '-j', 'DROP',
                '-m', 'comment', '--comment', f'sentinel:{reason}'
            ], check=True)
            
            # Persist to file
            self.blocked_ips.add(ip)
            with open(self.blocklist_file, 'a') as f:
                f.write(f"{ip}\n")
            
            print(f"[BLOCKED] {ip} - {reason}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to block {ip}: {e}")
            return False
    
    def block_multiple(self, ips: List[str], reason: str = "malicious"):
        """Block multiple IPs at once"""
        blocked_count = 0
        for ip in ips:
            if self.block_ip(ip, reason):
                blocked_count += 1
        return blocked_count
    
    def unblock_ip(self, ip: str):
        """Remove IP from blocklist"""
        try:
            subprocess.run([
                'iptables', '-D', 'INPUT',
                '-s', ip,
                '-j', 'DROP'
            ], check=True)
            
            self.blocked_ips.discard(ip)
            print(f"[UNBLOCKED] {ip}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to unblock {ip}: {e}")
            return False
    
    def list_blocked(self) -> List[str]:
        """Get list of currently blocked IPs"""
        return list(self.blocked_ips)
    
    def clear_all(self):
        """Remove all blocks (use with caution!)"""
        for ip in list(self.blocked_ips):
            self.unblock_ip(ip)


# Integration with agent
async def on_malicious_detection(log_data: dict):
    """Called when malicious activity detected"""
    blocker = IPBlocker()
    
    # Extract attacker IPs
    attackers = log_data.get('top_attackers', [])
    
    # Block top offenders (e.g., >100 requests in window)
    high_volume = [
        a['ip'] for a in attackers 
        if a['requests'] > 100
    ]
    
    if high_volume:
        blocked = blocker.block_multiple(high_volume, "high_volume_attack")
        print(f"Blocked {blocked} IPs from attack")
```

### Integration with Agent

Update `agent/main.py` to trigger blocking:

```python
# In run_agent() function, after detecting anomaly:

if trigger:
    msg = {
        "ts": ts,
        "window_ms": WINDOW_MS,
        "region": REGION,
        "asn": ASN,
        "method": m,
        "metrics": {
            "p95": round(p95, 2),
            "err_rate": round(err_rate, 4),
        },
        "z": {"lat": round(z_lat, 2), "err": round(z_err, 2)},
        "sample": ev.get("ip") and ip_hash(ip, SALT)
    }
    await pub("sentinel/diag", orjson.dumps(msg))
    
    # NEW: Trigger automatic blocking
    if AUTO_BLOCK:
        from tools.blocker import on_malicious_detection
        await on_malicious_detection({
            'top_attackers': [{'ip': ip, 'requests': ws.calls}]
        })
```

---

## 2. Rate Limiting

### Nginx Rate Limiting

Use nginx to rate limit based on IP hash:

```nginx
# /etc/nginx/conf.d/sentinel-ratelimit.conf

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=heavy:10m rate=10r/s;

# Map heavy methods
map $request_uri $is_heavy_method {
    default 0;
    ~*getProgramAccounts 1;
    ~*getLogs 1;
    ~*getSignaturesForAddress 1;
}

server {
    listen 80;
    server_name rpc.example.com;
    
    # General rate limit
    limit_req zone=general burst=200 nodelay;
    
    # Stricter limit for heavy methods
    if ($is_heavy_method) {
        limit_req zone=heavy burst=20 nodelay;
    }
    
    # Block known malicious IPs
    include /etc/sentinel/blocked_ips.nginx;
    
    location / {
        proxy_pass http://solana-rpc:8899;
        
        # Log for SentinelKarma
        access_log /var/log/nginx/rpc.jsonl json_combined;
    }
}
```

### Dynamic Blocklist for Nginx

Generate nginx blocklist from SentinelKarma logs:

```python
# tools/generate_nginx_blocklist.py
import json

def generate_nginx_blocklist(malicious_log_path: str, output_path: str):
    """Generate nginx blocklist from malicious logs"""
    
    blocked_ips = set()
    
    # Parse malicious logs
    with open(malicious_log_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                for attacker in data.get('top_attackers', []):
                    ip = attacker.get('ip')
                    requests = attacker.get('requests', 0)
                    
                    # Block if >50 requests in window
                    if ip and requests > 50:
                        blocked_ips.add(ip)
            except:
                continue
    
    # Write nginx config
    with open(output_path, 'w') as f:
        f.write("# Auto-generated by SentinelKarma\n")
        f.write(f"# Generated: {datetime.now()}\n\n")
        
        for ip in sorted(blocked_ips):
            f.write(f"deny {ip};\n")
    
    print(f"Generated blocklist with {len(blocked_ips)} IPs")
    
    # Reload nginx
    subprocess.run(['nginx', '-s', 'reload'])

# Run every 5 minutes
if __name__ == '__main__':
    generate_nginx_blocklist(
        '/data/malicious_logs/latest.log',
        '/etc/sentinel/blocked_ips.nginx'
    )
```

---

## 3. Shared Intelligence

### Download and Apply Peer Blocklists

Learn from other peers' detections:

```python
# tools/sync_blocklists.py
import asyncio
from infra.ipfs_gateway.client import IPFSGatewayClient
from solders.keypair import Keypair

async def sync_peer_blocklists(gateway_url: str, keypair: Keypair):
    """Download blocklists from other peers and apply"""
    
    client = IPFSGatewayClient(gateway_url, keypair)
    blocker = IPBlocker()
    
    # Query on-chain for recent reports
    reports = await get_recent_reports()  # From Solana contract
    
    for report in reports:
        try:
            # Download log from IPFS
            log_data = client.request_log(report.ipfs_cid)
            
            # Extract attackers
            attackers = parse_log(log_data['data'])
            
            # Calculate trust score based on reporter's karma
            trust_score = get_peer_karma(report.owner)
            
            # Only apply if high-trust peer (karma > 100)
            if trust_score > 100:
                ips_to_block = [
                    a['ip'] for a in attackers 
                    if a['requests'] > 100
                ]
                
                blocked = blocker.block_multiple(
                    ips_to_block, 
                    f"peer_intel:{report.owner[:8]}"
                )
                
                print(f"Applied {blocked} blocks from peer {report.owner[:8]}")
        
        except Exception as e:
            print(f"Failed to process report {report.ipfs_cid}: {e}")

# Run periodically
async def main():
    keypair = Keypair.from_base58_string(os.getenv("PEER_PRIVATE_KEY"))
    
    while True:
        await sync_peer_blocklists("http://gateway:8000", keypair)
        await asyncio.sleep(300)  # Every 5 minutes

if __name__ == '__main__':
    asyncio.run(main())
```

---

## 4. Attack Classification

### Identify Attack Types

Different attacks require different responses:

```python
# tools/attack_classifier.py

class AttackClassifier:
    """Classify attack types from log patterns"""
    
    @staticmethod
    def classify(log_data: dict) -> dict:
        """
        Returns:
        {
            'type': 'ddos' | 'resource_exhaustion' | 'scanning' | 'credential_stuffing',
            'severity': 'low' | 'medium' | 'high' | 'critical',
            'confidence': 0.0-1.0,
            'recommended_action': str
        }
        """
        metrics = log_data.get('metrics', {})
        z_scores = log_data.get('z', {})
        method = log_data.get('method', '')
        
        # DDoS: High volume, normal error rate
        if metrics.get('requests', 0) > 1000 and metrics.get('err_rate', 0) < 0.1:
            return {
                'type': 'ddos',
                'severity': 'critical',
                'confidence': 0.9,
                'recommended_action': 'block_ips_immediately'
            }
        
        # Resource Exhaustion: Heavy methods, high latency
        if method in ['getProgramAccounts', 'getLogs'] and z_scores.get('lat', 0) > 5:
            return {
                'type': 'resource_exhaustion',
                'severity': 'high',
                'confidence': 0.85,
                'recommended_action': 'rate_limit_heavy_methods'
            }
        
        # Scanning/Fuzzing: High error rate
        if metrics.get('err_rate', 0) > 0.3:
            return {
                'type': 'scanning',
                'severity': 'medium',
                'confidence': 0.8,
                'recommended_action': 'block_ips_temporary'
            }
        
        # Credential Stuffing: Repeated auth failures
        if method == 'authenticate' and metrics.get('err_rate', 0) > 0.5:
            return {
                'type': 'credential_stuffing',
                'severity': 'high',
                'confidence': 0.75,
                'recommended_action': 'block_ips_and_alert'
            }
        
        return {
            'type': 'unknown',
            'severity': 'low',
            'confidence': 0.5,
            'recommended_action': 'monitor'
        }


# Use in agent
async def handle_attack(log_data: dict):
    """Handle detected attack based on classification"""
    
    classification = AttackClassifier.classify(log_data)
    
    print(f"[ATTACK] Type: {classification['type']}, "
          f"Severity: {classification['severity']}, "
          f"Confidence: {classification['confidence']}")
    
    action = classification['recommended_action']
    
    if action == 'block_ips_immediately':
        # Block all attackers permanently
        blocker = IPBlocker()
        attackers = extract_attackers(log_data)
        blocker.block_multiple([a['ip'] for a in attackers], 'ddos')
    
    elif action == 'rate_limit_heavy_methods':
        # Update nginx rate limits
        update_nginx_rate_limits(method=log_data['method'], rate='5r/s')
    
    elif action == 'block_ips_temporary':
        # Block for 1 hour
        blocker = IPBlocker()
        attackers = extract_attackers(log_data)
        blocker.block_multiple([a['ip'] for a in attackers], 'scanning')
        # Schedule unblock after 1 hour
        asyncio.create_task(unblock_after_delay(attackers, 3600))
    
    elif action == 'block_ips_and_alert':
        # Block and notify security team
        blocker = IPBlocker()
        attackers = extract_attackers(log_data)
        blocker.block_multiple([a['ip'] for a in attackers], 'credential_stuffing')
        send_alert_to_security_team(classification, attackers)
```

---

## 5. Automated Response System

### Complete Integration

Put it all together in a response daemon:

```python
# tools/response_daemon.py
import asyncio
import os
from aiomqtt import Client
import orjson

class ResponseDaemon:
    """Automated attack response system"""
    
    def __init__(self):
        self.blocker = IPBlocker()
        self.classifier = AttackClassifier()
        self.mqtt_url = os.getenv("MQTT_URL", "mqtt://mosquitto:1883")
        
        # Configuration
        self.auto_block = os.getenv("AUTO_BLOCK", "true").lower() == "true"
        self.min_confidence = float(os.getenv("MIN_CONFIDENCE", "0.7"))
        self.block_threshold = int(os.getenv("BLOCK_THRESHOLD", "50"))
    
    async def run(self):
        """Main loop: listen to MQTT and respond to attacks"""
        
        u = urlparse(self.mqtt_url)
        host = u.hostname or "localhost"
        port = u.port or 1883
        
        while True:
            try:
                async with Client(host, port) as client:
                    await client.subscribe("sentinel/diag")
                    
                    async with client.messages() as messages:
                        async for msg in messages:
                            try:
                                data = orjson.loads(msg.payload)
                                await self.handle_alert(data)
                            except Exception as e:
                                print(f"[ERROR] Failed to process alert: {e}")
            
            except Exception as e:
                print(f"[ERROR] MQTT connection failed: {e}")
                await asyncio.sleep(5)
    
    async def handle_alert(self, data: dict):
        """Process incoming alert and take action"""
        
        # Classify attack
        classification = self.classifier.classify(data)
        
        # Only act on high-confidence detections
        if classification['confidence'] < self.min_confidence:
            return
        
        print(f"[ALERT] {classification['type']} attack detected "
              f"(confidence: {classification['confidence']:.2f})")
        
        # Extract attackers from sample IP
        sample_ip = data.get('sample', '').replace('iphash:', '')
        
        # In production, you'd reverse the hash or use the full log
        # For now, we'll use the sample as a placeholder
        
        if self.auto_block and classification['severity'] in ['high', 'critical']:
            # Take automated action
            await self.execute_response(classification, data)
        else:
            # Just log for manual review
            print(f"[MANUAL] Review required for {classification['type']} attack")
    
    async def execute_response(self, classification: dict, data: dict):
        """Execute the recommended response action"""
        
        action = classification['recommended_action']
        
        if 'block' in action:
            # Block IPs (in production, extract from full log)
            print(f"[ACTION] Executing: {action}")
            
            # Upload to IPFS for sharing
            # Submit on-chain report
            # Notify other peers
        
        # Log action taken
        self.log_action(classification, data)
    
    def log_action(self, classification: dict, data: dict):
        """Log all automated actions for audit"""
        with open('/var/log/sentinel/actions.log', 'a') as f:
            f.write(orjson.dumps({
                'timestamp': int(time.time()),
                'classification': classification,
                'data': data
            }).decode() + '\n')


if __name__ == '__main__':
    daemon = ResponseDaemon()
    asyncio.run(daemon.run())
```

---

## 6. Dashboard & Monitoring

### Real-Time Attack Dashboard

```python
# tools/dashboard.py
from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Main dashboard view"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get current attack statistics"""
    
    blocker = IPBlocker()
    
    # Read recent logs
    attacks_last_hour = count_attacks_last_hour()
    blocked_ips = len(blocker.list_blocked())
    
    return jsonify({
        'attacks_last_hour': attacks_last_hour,
        'blocked_ips': blocked_ips,
        'active_peers': get_active_peer_count(),
        'recent_attacks': get_recent_attacks(limit=10)
    })

@app.route('/api/blocklist')
def get_blocklist():
    """Get current blocklist"""
    blocker = IPBlocker()
    return jsonify({
        'blocked_ips': blocker.list_blocked()
    })

@app.route('/api/unblock/<ip>', methods=['POST'])
def unblock_ip(ip):
    """Manually unblock an IP"""
    blocker = IPBlocker()
    success = blocker.unblock_ip(ip)
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## 7. Best Practices

### Do's

✅ **Start with monitoring only** - Don't auto-block until you're confident  
✅ **Whitelist critical IPs** - Your own infrastructure, partners, etc.  
✅ **Set confidence thresholds** - Only act on high-confidence detections  
✅ **Log all actions** - Audit trail for compliance  
✅ **Test in staging** - Verify blocks don't affect legitimate users  
✅ **Use temporary blocks** - Unblock after 1-24 hours for non-critical attacks  
✅ **Share intelligence** - Upload validated threats to IPFS  

### Don'ts

❌ **Don't block without verification** - False positives hurt users  
❌ **Don't block entire subnets** - Too broad, affects innocents  
❌ **Don't ignore whitelists** - Always check before blocking  
❌ **Don't auto-block low-confidence** - Manual review required  
❌ **Don't forget to unblock** - Temporary blocks should expire  
❌ **Don't skip logging** - You need audit trails  

---

## 8. Production Deployment

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  agent:
    build: ./agent-python
    environment:
      - AUTO_BLOCK=true
      - MIN_CONFIDENCE=0.8
      - BLOCK_THRESHOLD=100
    volumes:
      - /var/log/sentinel:/var/log/sentinel
    cap_add:
      - NET_ADMIN  # Required for iptables
    network_mode: host

  response-daemon:
    build: ./agent-python
    command: python3 tools/response_daemon.py
    environment:
      - MQTT_URL=mqtt://mosquitto:1883
      - AUTO_BLOCK=true
    cap_add:
      - NET_ADMIN
    network_mode: host

  dashboard:
    build: ./agent-python
    command: python3 tools/dashboard.py
    ports:
      - "5000:5000"
    volumes:
      - /var/log/sentinel:/var/log/sentinel:ro
```

### Systemd Service

```ini
# /etc/systemd/system/sentinel-response.service
[Unit]
Description=SentinelKarma Response Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/sentinelkarma
ExecStart=/usr/bin/python3 tools/response_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 9. Testing

### Simulate Attack

```bash
# Test DDoS detection
for i in {1..1000}; do
  curl http://localhost:8899 -X POST \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' &
done

# Check if blocked
tail -f /var/log/sentinel/actions.log
```

### Verify Blocking

```bash
# Check iptables rules
iptables -L INPUT -n -v | grep sentinel

# Check nginx blocklist
cat /etc/sentinel/blocked_ips.nginx

# Test blocked IP
curl --interface <blocked_ip> http://localhost:8899
# Should timeout or return 403
```

---

## Summary

**Attack Response Pipeline:**

1. **Detect** → Agent identifies anomaly in 250ms window
2. **Classify** → Determine attack type and severity
3. **Extract** → Get attacker IPs from logs
4. **Block** → Apply firewall rules / rate limits
5. **Share** → Upload to IPFS, submit on-chain
6. **Learn** → Other peers download and apply

**Key Components:**

- `blocker.py` - Automatic IP blocking with iptables
- `attack_classifier.py` - ML-based attack classification
- `response_daemon.py` - Automated response system
- `sync_blocklists.py` - Learn from peer intelligence
- `dashboard.py` - Real-time monitoring UI

**Result:** Attacks stopped in <1 second, shared across network, continuously improving defense.
