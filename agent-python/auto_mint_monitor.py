#!/usr/bin/env python3
"""
Automated NFT minting monitor for Sentinel
Watches the log database and mints NFTs when new logs are added
"""
import json
import asyncio
import hashlib
import time
from pathlib import Path
from typing import Dict, Set
import aiohttp
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet, Program, Idl, Context
import subprocess

# Configuration
LOG_DATABASE_URL = "http://localhost:8080"  # Your log server
CHECK_INTERVAL = 10  # Check every 10 seconds
PROGRAM_ID = Pubkey.from_string("7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7")
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

# Track minted logs
minted_logs: Set[str] = set()

def get_associated_token_address(mint: Pubkey, owner: Pubkey) -> Pubkey:
    """Calculate associated token address"""
    seeds = [bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)]
    return Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)[0]

def compute_log_hash(log_data: dict) -> bytes:
    """Compute SHA256 hash of log data"""
    log_str = json.dumps(log_data, sort_keys=True)
    return hashlib.sha256(log_str.encode()).digest()

async def fetch_new_logs(session: aiohttp.ClientSession) -> list:
    """Fetch new logs from the database"""
    try:
        async with session.get(f"{LOG_DATABASE_URL}/api/logs") as resp:
            if resp.status == 200:
                logs = await resp.json()
                return [log for log in logs if log['id'] not in minted_logs]
            return []
    except Exception as e:
        print(f"⚠️  Error fetching logs: {e}")
        return []

def create_nft_mint() -> tuple[str, str]:
    """Create a new NFT mint using spl-token CLI"""
    try:
        # Create temporary keypair
        temp_keypair = f"/tmp/nft_mint_{int(time.time())}.json"
        
        # Generate keypair
        subprocess.run(
            ["solana-keygen", "new", "--no-bip39-passphrase", 
             "--outfile", temp_keypair, "--force"],
            capture_output=True,
            check=True
        )
        
        # Get pubkey
        result = subprocess.run(
            ["solana-keygen", "pubkey", temp_keypair],
            capture_output=True,
            text=True,
            check=True
        )
        nft_mint = result.stdout.strip()
        
        # Create token with 0 decimals
        subprocess.run(
            ["spl-token", "create-token", "--decimals", "0", temp_keypair],
            capture_output=True,
            check=True
        )
        
        # Clean up
        Path(temp_keypair).unlink()
        
        return nft_mint, "success"
    except Exception as e:
        return None, str(e)

async def mint_nft_for_log(
    program: Program,
    wallet: Wallet,
    log_data: dict
) -> bool:
    """Mint an NFT for a specific log entry"""
    try:
        log_id = log_data['id']
        print(f"\n🎨 Minting NFT for log: {log_id}")
        
        # Create NFT mint
        print("   Creating NFT mint...")
        nft_mint_str, error = create_nft_mint()
        if not nft_mint_str:
            print(f"   ❌ Failed to create mint: {error}")
            return False
        
        nft_mint = Pubkey.from_string(nft_mint_str)
        print(f"   ✅ NFT Mint: {nft_mint}")
        
        # Compute hash from log data
        log_hash = compute_log_hash(log_data)
        hash_array = list(log_hash)
        
        # Use log ID as database address (or create a proper one)
        db_addr = Pubkey.from_string(log_data.get('db_address', wallet.public_key))
        
        # Derive PDAs
        state_pda, _ = Pubkey.find_program_address([b"state"], PROGRAM_ID)
        peer_pda, _ = Pubkey.find_program_address(
            [b"peer", bytes(wallet.public_key)], 
            PROGRAM_ID
        )
        user_nft_ata = get_associated_token_address(nft_mint, wallet.public_key)
        post_pda, _ = Pubkey.find_program_address(
            [b"post", bytes(nft_mint)], 
            PROGRAM_ID
        )
        
        print(f"   Post PDA: {post_pda}")
        print(f"   Hash: {log_hash.hex()[:16]}...")
        
        # Call mint_nft instruction
        tx = await program.rpc["mint_nft"](
            hash_array,
            db_addr,
            ctx=Context(
                accounts={
                    "user": wallet.public_key,
                    "state": state_pda,
                    "peer": peer_pda,
                    "nft_mint": nft_mint,
                    "user_nft_ata": user_nft_ata,
                    "post": post_pda,
                    "token_program": TOKEN_PROGRAM_ID,
                    "associated_token_program": ASSOCIATED_TOKEN_PROGRAM_ID,
                    "system_program": SYS_PROGRAM_ID,
                    "rent": RENT,
                }
            )
        )
        
        print(f"   ✅ NFT minted!")
        print(f"   Transaction: {tx}")
        
        # Mark as minted
        minted_logs.add(log_id)
        
        # Store mapping
        mapping = {
            "log_id": log_id,
            "nft_mint": str(nft_mint),
            "post_pda": str(post_pda),
            "transaction": str(tx),
            "timestamp": time.time()
        }
        
        # Save to file
        mappings_file = Path("nft_mappings.json")
        mappings = []
        if mappings_file.exists():
            with open(mappings_file) as f:
                mappings = json.load(f)
        mappings.append(mapping)
        with open(mappings_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error minting NFT: {e}")
        import traceback
        traceback.print_exc()
        return False

async def monitor_loop():
    """Main monitoring loop"""
    print("🚀 Sentinel Auto-Mint Monitor")
    print("=" * 50)
    print(f"📍 Program ID: {PROGRAM_ID}")
    print(f"🌐 Log Database: {LOG_DATABASE_URL}")
    print(f"⏱️  Check Interval: {CHECK_INTERVAL}s")
    print()
    
    # Setup Solana connection
    client = AsyncClient("http://localhost:8899", commitment=Confirmed)
    
    # Load wallet
    wallet_path = Path.home() / ".config" / "solana" / "id.json"
    with open(wallet_path) as f:
        keypair = Keypair.from_bytes(json.load(f))
    wallet = Wallet(keypair)
    
    print(f"👤 Wallet: {wallet.public_key}")
    print()
    
    # Create provider
    provider = Provider(client, wallet)
    
    # Load IDL
    sentinel_dir = Path(__file__).parent.parent / "sentinel"
    idl_path = sentinel_dir / "target" / "idl" / "sentinel.json"
    with open(idl_path) as f:
        idl = Idl.from_json(json.dumps(json.load(f)))
    
    program = Program(idl, PROGRAM_ID, provider)
    
    # Check if peer is active
    peer_pda, _ = Pubkey.find_program_address(
        [b"peer", bytes(wallet.public_key)], 
        PROGRAM_ID
    )
    
    try:
        peer_account = await program.account["PeerState"].fetch(peer_pda)
        if not peer_account.active:
            print("❌ Wallet is not an active peer!")
            print("   Run: python3 mint_nft.py")
            return
        print(f"✅ Peer active (Karma: {peer_account.karma})")
    except:
        print("❌ Wallet is not a network member!")
        print("   Run: python3 mint_nft.py")
        return
    
    print()
    print("👀 Monitoring for new logs...")
    print()
    
    # Create HTTP session
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Fetch new logs
                new_logs = await fetch_new_logs(session)
                
                if new_logs:
                    print(f"📥 Found {len(new_logs)} new log(s)")
                    
                    for log in new_logs:
                        success = await mint_nft_for_log(program, wallet, log)
                        if success:
                            print(f"✅ Successfully minted NFT for log {log['id']}")
                        else:
                            print(f"❌ Failed to mint NFT for log {log['id']}")
                        
                        # Small delay between mints
                        await asyncio.sleep(2)
                
                # Wait before next check
                await asyncio.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping monitor...")
                break
            except Exception as e:
                print(f"�� Error in monitor loop: {e}")
                await asyncio.sleep(CHECK_INTERVAL)
    
    await client.close()
    print("👋 Monitor stopped")

def main():
    """Entry point"""
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
