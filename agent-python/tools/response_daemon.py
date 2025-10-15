import asyncio
import os
import time
import sys
from urllib.parse import urlparse
import orjson
from aiomqtt import Client

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.blocker import IPBlocker
from tools.attack_classifier import AttackClassifier


class ResponseDaemon:
    """Automated attack response system"""
    
    def __init__(self):
        self.blocker = IPBlocker()
        self.classifier = AttackClassifier()
        self.mqtt_url = os.getenv("MQTT_URL", "mqtt://mosquitto:1883")
        
        self.auto_block = os.getenv("AUTO_BLOCK", "false").lower() in ("true", "1", "yes")
        self.min_confidence = float(os.getenv("MIN_CONFIDENCE", "0.75"))
        self.block_threshold = int(os.getenv("BLOCK_THRESHOLD", "100"))
        self.dry_run = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")
        
        self.actions_log = os.getenv("ACTIONS_LOG", "/data/actions.log")
        
        print(f"[DAEMON] Response Daemon initialized")
        print(f"[DAEMON] Auto-block: {self.auto_block}")
        print(f"[DAEMON] Min confidence: {self.min_confidence}")
        print(f"[DAEMON] Dry run: {self.dry_run}")
    
    async def run(self):
        """Main loop: listen to MQTT and respond to attacks"""
        u = urlparse(self.mqtt_url)
        host = u.hostname or "localhost"
        port = u.port or 1883
        
        print(f"[DAEMON] Connecting to MQTT at {host}:{port}")
        
        while True:
            try:
                async with Client(host, port) as client:
                    await client.subscribe("sentinel/diag")
                    print("[DAEMON] Subscribed to sentinel/diag")
                    
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
        classification = self.classifier.classify(data)
        
        if classification['confidence'] < self.min_confidence:
            return
        
        severity = classification['severity']
        attack_type = classification['type']
        confidence = classification['confidence']
        
        print(f"\n[ALERT] {attack_type.upper()} detected")
        print(f"[ALERT] Severity: {severity}, Confidence: {confidence:.0%}")
        
        for indicator in classification['indicators']:
            print(f"[ALERT]   - {indicator}")
        
        if self.auto_block and self.classifier.should_auto_block(classification, self.min_confidence):
            await self.execute_response(classification, data)
        else:
            print(f"[ALERT] Manual review required (auto_block={self.auto_block})")
        
        self.log_action(classification, data)
    
    async def execute_response(self, classification: dict, data: dict):
        """Execute the recommended response action"""
        action = classification['recommended_action']
        
        print(f"[ACTION] Executing: {action}")
        
        if self.dry_run:
            print(f"[DRY-RUN] Would execute: {action}")
            return
        
        if action == 'block_ips_immediately':
            await self.block_attackers(data, reason='ddos', permanent=True)
        
        elif action == 'rate_limit_heavy_methods':
            print(f"[ACTION] Rate limiting method: {data.get('method')}")
        
        elif action == 'block_ips_temporary':
            await self.block_attackers(data, reason='scanning', duration=3600)
        
        elif action == 'block_ips_and_alert':
            await self.block_attackers(data, reason='credential_stuffing', permanent=True)
            await self.send_alert(classification, data)
        
        elif action == 'rate_limit':
            print(f"[ACTION] Applying rate limits")
        
        else:
            print(f"[ACTION] Monitoring only")
    
    async def block_attackers(self, data: dict, reason: str, permanent: bool = False, duration: int = None):
        """Block attacker IPs from the alert data"""
        sample = data.get('sample', '')
        
        if not sample:
            print("[ACTION] No sample IP to block")
            return
        
        ip_hash = sample.replace('iphash:', '')
        
        print(f"[ACTION] Would block IP hash: {ip_hash}")
        print(f"[ACTION] Reason: {reason}, Permanent: {permanent}")
        
        if duration:
            print(f"[ACTION] Duration: {duration}s")
    
    async def send_alert(self, classification: dict, data: dict):
        """Send alert to security team"""
        print(f"[ALERT] Sending notification to security team")
        print(f"[ALERT] Attack: {classification['type']}")
        print(f"[ALERT] Severity: {classification['severity']}")
    
    def log_action(self, classification: dict, data: dict):
        """Log all automated actions for audit"""
        try:
            os.makedirs(os.path.dirname(self.actions_log), exist_ok=True)
            
            with open(self.actions_log, 'ab') as f:
                log_entry = {
                    'timestamp': int(time.time()),
                    'classification': classification,
                    'data': {
                        'method': data.get('method'),
                        'region': data.get('region'),
                        'asn': data.get('asn'),
                        'metrics': data.get('metrics'),
                        'z': data.get('z')
                    },
                    'auto_block': self.auto_block,
                    'dry_run': self.dry_run
                }
                f.write(orjson.dumps(log_entry) + b'\n')
        except Exception as e:
            print(f"[ERROR] Failed to log action: {e}")


async def main():
    """Entry point"""
    daemon = ResponseDaemon()
    
    try:
        await daemon.run()
    except KeyboardInterrupt:
        print("\n[DAEMON] Shutting down...")
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        raise


if __name__ == '__main__':
    import uvloop
    uvloop.install()
    asyncio.run(main())
