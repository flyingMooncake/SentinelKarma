#!/usr/bin/env python3
"""
Auto Mint Monitor - Monitors data/contract_data for new files
Automatically processes files that are:
- Newer than 10 minutes
- Not already uploaded to HTTP server
"""

import os
import sys
import time
import hashlib
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Config
CONTRACT_DATA_DIR = "./data/contract_data"
KEYPAIR_PATH = "./sentinel/deploy-keypair.json"
CHECK_INTERVAL = 60  # seconds

# Auto-detect IP
def get_wsl_ip():
    """Get WSL IP address"""
    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True, text=True
        )
        return result.stdout.strip().split()[0]
    except:
        return "172.19.12.161"

LOG_SERVER_URL = f"http://{get_wsl_ip()}:9000"

def get_pubkey():
    """Get pubkey from keypair"""
    result = subprocess.run(
        ['solana-keygen', 'pubkey', KEYPAIR_PATH],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def compute_hash(filepath):
    """Compute SHA256"""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()

def is_recent(filepath, minutes=10):
    """Check if file is newer than N minutes"""
    mtime = os.path.getmtime(filepath)
    file_time = datetime.fromtimestamp(mtime)
    cutoff = datetime.now() - timedelta(minutes=minutes)
    return file_time > cutoff

def is_uploaded(file_hash):
    """Check if already on server"""
    log_id = file_hash[:16]
    try:
        r = requests.get(f"{LOG_SERVER_URL}/logs/{log_id}/metadata", timeout=5)
        return r.status_code == 200
    except:
        return False

def upload_file(filepath, pubkey):
    """Upload to server"""
    filename = os.path.basename(filepath)
    headers = {
        'X-Peer-Pubkey': pubkey,
        'X-Timestamp': str(int(time.time())),
        'X-Signature': 'test',
    }
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            r = requests.post(f"{LOG_SERVER_URL}/logs", headers=headers, files=files, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        print(f"  [ERROR] Upload failed: {e}")
        return None

def process_file(filepath, pubkey):
    """Process one file"""
    filename = os.path.basename(filepath)
    print(f"\n[{filename}]")
    
    if not is_recent(filepath):
        print(f"  [SKIP] Older than 10 minutes")
        return False
    
    file_hash = compute_hash(filepath)
    print(f"  Hash: {file_hash[:16]}...")
    
    if is_uploaded(file_hash):
        print(f"  [SKIP] Already uploaded")
        return False
    
    print(f"  Uploading...")
    result = upload_file(filepath, pubkey)
    
    if result:
        print(f"  ✓ Uploaded! ID: {result['log_id']}")
        print(f"    URL: {result['url']}")
        return True
    else:
        print(f"  ✗ Upload failed")
        return False

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        Auto Mint Monitor - FULL Mode                      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    pubkey = get_pubkey()
    print(f"[INFO] Payer: {pubkey}")
    print(f"[INFO] Monitoring: {CONTRACT_DATA_DIR}")
    print(f"[INFO] Check interval: {CHECK_INTERVAL}s")
    print(f"[INFO] File age threshold: 10 minutes")
    print()
    
    processed = set()
    
    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{ts}] Scanning...")
            
            log_dir = Path(CONTRACT_DATA_DIR)
            if not log_dir.exists():
                print(f"[WARN] Directory not found: {CONTRACT_DATA_DIR}")
                time.sleep(CHECK_INTERVAL)
                continue
            
            log_files = sorted(log_dir.glob("*.log"))
            new_files = [f for f in log_files if str(f) not in processed]
            
            if not new_files:
                print("[INFO] No new files")
            else:
                print(f"[INFO] Found {len(new_files)} new file(s)")
                for f in new_files:
                    if process_file(str(f), pubkey):
                        processed.add(str(f))
                    else:
                        processed.add(str(f))  # Mark as processed even if skipped
                    time.sleep(1)
            
            print(f"\n[INFO] Next check in {CHECK_INTERVAL}s...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopped by user")
        return 0

if __name__ == "__main__":
    sys.exit(main())