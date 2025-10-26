#!/bin/bash
# Simple NFT sync - runs populate script every 30 seconds

cd /home/water/SentinelKarma

echo "Starting NFT sync daemon..."
echo "Will sync every 30 seconds"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Syncing NFTs..."
    python3 scripts/populate_nft_mappings.py 2>&1 | grep -E "(Found|Saved|Error)"
    sleep 30
done
