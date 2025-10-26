#!/usr/bin/env python3
"""
NFT Sync Daemon - Runs continuously to sync NFT mappings from blockchain
Runs on startup and refreshes every 30 seconds
"""

import json
import asyncio
import time
from pathlib import Path
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

SOLANA_RPC = "http://localhost:8899"
WALLET_PATH = Path.home() / ".config" / "solana" / "id.json"
PROGRAM_ID = Pubkey.from_string("7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7")
OUTPUT_FILE = Path("/home/water/SentinelKarma/nft_mappings.json")
SYNC_INTERVAL = 30  # seconds

async def sync_nfts():
    """Sync NFT mappings from blockchain"""
    try:
        # Load wallet
        with open(WALLET_PATH) as f:
            keypair = Keypair.from_bytes(json.load(f))
        
        wallet_pubkey = keypair.pubkey()
        
        # Connect to Solana
        client = AsyncClient(SOLANA_RPC, commitment=Confirmed)
        
        try:
            # Get all transactions for this wallet
            sigs_response = await client.get_signatures_for_address(wallet_pubkey, limit=1000)
            
            if not sigs_response.value:
                return []
            
            signatures = sigs_response.value
            
            # Parse transactions to find mint_nft calls
            mappings = []
            
            for sig_info in signatures:
                sig = sig_info.signature
                
                # Get transaction details
                tx_response = await client.get_transaction(
                    sig,
                    encoding="jsonParsed",
                    max_supported_transaction_version=0
                )
                
                if not tx_response.value:
                    continue
                
                tx = tx_response.value
                
                # Check if this is a mint_nft transaction
                if tx.transaction.message.account_keys:
                    program_found = False
                    for key in tx.transaction.message.account_keys:
                        if hasattr(key, 'pubkey'):
                            if str(key.pubkey) == str(PROGRAM_ID):
                                program_found = True
                                break
                    
                    if program_found:
                        timestamp = tx.block_time if tx.block_time else 0
                        log_url = f"http://localhost:9000/logs/unknown"
                        
                        mapping = {
                            "filename": f"minted_{timestamp}.log",
                            "log_url": log_url,
                            "hash": f"tx_{sig}",
                            "nft_tx": str(sig),
                            "timestamp": timestamp
                        }
                        
                        mappings.append(mapping)
            
            return mappings
            
        finally:
            await client.close()
            
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")
        return []

async def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║              NFT Sync Daemon - Starting                   ║")
    print("╚════════════════════════════════════���═══════════════════════╝")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Sync interval: {SYNC_INTERVAL}s")
    print()
    
    while True:
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Syncing NFTs from blockchain...")
            
            mappings = await sync_nfts()
            
            if mappings:
                # Save to file
                OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(OUTPUT_FILE, 'w') as f:
                    json.dump(mappings, f, indent=2)
                
                print(f"[{timestamp}] ✓ Synced {len(mappings)} NFTs")
            else:
                print(f"[{timestamp}] No NFTs found")
            
        except Exception as e:
            print(f"[ERROR] {e}")
        
        # Wait before next sync
        await asyncio.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
