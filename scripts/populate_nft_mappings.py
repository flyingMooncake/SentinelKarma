#!/usr/bin/env python3
"""
Populate nft_mappings.json from uploaded logs in HTTP server
Only includes NFTs that have actual log data
"""

import json
import time
from pathlib import Path

OUTPUT_FILE = Path("./nft_mappings.json")
LOGS_DIR = Path("./data/logs")

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          Populate NFT Mappings from HTTP Server Logs      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Get actual uploaded logs from HTTP server
    print(f"Scanning {LOGS_DIR} for uploaded logs...")
    log_files = []
    if LOGS_DIR.exists():
        for meta_file in sorted(LOGS_DIR.glob("*.meta"), reverse=True):
            try:
                with open(meta_file) as f:
                    metadata = json.load(f)
                    log_files.append(metadata)
            except:
                continue
    
    print(f"Found {len(log_files)} uploaded logs with metadata")
    print()
    
    # Create mappings from real logs
    mappings = []
    for i, log in enumerate(log_files):
        mapping = {
            "filename": log.get("filename", "unknown.log"),
            "log_url": f"http://localhost:9000/logs/{log['log_id']}",
            "hash": log.get("hash", log['log_id']),
            "nft_tx": log.get("hash", log['log_id']),
            "timestamp": log.get("timestamp", int(time.time()))
        }
        mappings.append(mapping)
        print(f"[{i+1}/{len(log_files)}] {log['log_id']} - {log.get('filename')}")
    
    # Save to file
    print()
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)
    
    print(f"✓ Saved {len(mappings)} NFT mappings to {OUTPUT_FILE}")
    print(f"  All mappings point to real uploaded logs")

if __name__ == "__main__":
    main()
