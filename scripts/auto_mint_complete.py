#!/usr/bin/env python3
"""
Complete Auto Mint Monitor
- Monitors data/malicious_logs for new attack logs (from saver.py)
- Uploads to HTTP log server
- Mints NFTs on Sentinel contract
"""

import os
import sys
import time
import hashlib
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import requests

# Solana/Anchor imports
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet, Program, Idl, Context

# Load configuration from file
def load_config():
    """Load configuration from auto_mint.conf"""
    config = {}
    config_file = Path(__file__).parent / "auto_mint.conf"
    
    if config_file.exists():
        with open(config_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove inline comments
                    value = value.split('#')[0].strip().strip('"')
                    config[key.strip()] = value
    
    return config

# Load config
CONFIG = load_config()

# Config with environment variable override
CONTRACT_DATA_DIR = os.getenv("CONTRACT_DATA_DIR", CONFIG.get("CONTRACT_DATA_DIR", "./data/contract_data"))
SENTINEL_DIR = os.getenv("SENTINEL_DIR", CONFIG.get("SENTINEL_DIR", "./sentinel"))
WALLET_PATH = os.path.expanduser(os.getenv("WALLET_PATH", CONFIG.get("WALLET_PATH", "~/.config/solana/id.json")))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", CONFIG.get("CHECK_INTERVAL", "30")))
FILE_AGE_MINUTES = int(os.getenv("FILE_AGE_MINUTES", CONFIG.get("FILE_AGE_MINUTES", "10")))
SOLANA_RPC = os.getenv("SOLANA_RPC_URL", CONFIG.get("SOLANA_RPC_URL", "http://localhost:8899"))

# Burst protection settings
OVERBURST_DURATION = int(CONFIG.get("OVERBURST_DURATION", "180"))
BURST_COOLDOWN = int(CONFIG.get("BURST_COOLDOWN", "10"))
BURST_DURATION = int(CONFIG.get("BURST_DURATION", "5"))
BURST_THRESHOLD = int(CONFIG.get("BURST_THRESHOLD", "5"))
MINT_DELAY = int(CONFIG.get("MINT_DELAY", "2"))

# Program ID
PROGRAM_ID = Pubkey.from_string("7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7")
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

# Log server URLs
# For uploading: always use localhost (running on host)
LOG_SERVER_URL = os.getenv("LOG_SERVER_URL", "http://localhost:9000")

# For NFT metadata: use public IP so other peers can access
def get_public_log_url():
    """Get public-facing log server URL for NFT metadata"""
    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True, text=True
        )
        ip = result.stdout.strip().split()[0]
        if ip and ip != "127.0.0.1":
            return f"http://{ip}:9000"
    except:
        pass
    return "http://localhost:9000"

PUBLIC_LOG_URL = os.getenv("PUBLIC_LOG_URL", get_public_log_url())

def get_associated_token_address(mint: Pubkey, owner: Pubkey) -> Pubkey:
    """Calculate ATA"""
    seeds = [bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)]
    return Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)[0]

def compute_hash(filepath: str) -> str:
    """Compute SHA256 of file"""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()

def is_recent(filepath: str, minutes: int = FILE_AGE_MINUTES) -> bool:
    """Check if file is newer than N minutes"""
    mtime = os.path.getmtime(filepath)
    file_time = datetime.fromtimestamp(mtime)
    cutoff = datetime.now() - timedelta(minutes=minutes)
    return file_time > cutoff
def check_if_uploaded(file_hash: str) -> bool:
    """Check if log already exists on HTTP server"""
    log_id = file_hash[:16]
    try:
        r = requests.get(f"{LOG_SERVER_URL}/logs/{log_id}/metadata", timeout=5)
        return r.status_code == 200
    except:
        return False

def upload_to_server(filepath: str, pubkey: str) -> Optional[Dict]:
    """Upload log to HTTP server"""
    filename = os.path.basename(filepath)
    headers = {
        'X-Peer-Pubkey': pubkey,
        'X-Timestamp': str(int(time.time())),
        'X-Signature': 'test',  # Testing mode
    }
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            r = requests.post(
                f"{LOG_SERVER_URL}/logs",
                headers=headers,
                files=files,
                timeout=30
            )
        if r.status_code == 200:
            return r.json()
        else:
            print(f"    [ERROR] Upload failed: {r.status_code}")
            return None
    except Exception as e:
        print(f"    [ERROR] Upload exception: {e}")
        return None

def create_nft_mint() -> Optional[str]:
    """Create NFT mint using spl-token"""
    try:
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
        
        return nft_mint
    except Exception as e:
        print(f"    [ERROR] Failed to create mint: {e}")
        return None

async def mint_nft_on_chain(
    program: Program,
    wallet: Wallet,
    log_hash: bytes,
    log_url: str
) -> Optional[str]:
    """Mint NFT on Sentinel contract"""
    try:
        # Create NFT mint
        print("    Creating NFT mint...")
        nft_mint_str = create_nft_mint()
        if not nft_mint_str:
            return None
        
        nft_mint = Pubkey.from_string(nft_mint_str)
        print(f"    NFT Mint: {nft_mint}")
        
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
        
        # Convert hash to array
        hash_array = list(log_hash)
        
        # Use a dummy db_addr (could be derived from log_url)
        db_addr = Keypair().pubkey()
        
        # Call mint_nft
        print("    Calling mint_nft instruction...")
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
        
        print(f"    ✓ NFT minted! TX: {tx}")
        return str(tx)
        
    except Exception as e:
        print(f"    [ERROR] Mint failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def process_file(
    filepath: str,
    program: Program,
    wallet: Wallet,
    pubkey_str: str
) -> bool:
    """Process one log file: upload and mint"""
    filename = os.path.basename(filepath)
    print(f"\n[{filename}]")
    
    # Check age
    if not is_recent(filepath):
        print(f"  [SKIP] Older than {FILE_AGE_MINUTES} minutes")
        return False
    
    # Compute hash
    file_hash = compute_hash(filepath)
    hash_bytes = bytes.fromhex(file_hash)
    print(f"  Hash: {file_hash[:16]}...")
    
    # Check if already uploaded (and therefore already minted)
    if check_if_uploaded(file_hash):
        print(f"  [SKIP] Already uploaded and minted")
        return False
    
    # Upload to server
    print("  Uploading to log server...")
    upload_result = upload_to_server(filepath, pubkey_str)
    
    if not upload_result:
        print("  [ERROR] Upload failed")
        return False
    
    log_url = upload_result['url']
    print(f"  ✓ Uploaded! URL: {log_url}")
    
    # Mint NFT
    print("  Minting NFT on Sentinel...")
    tx = await mint_nft_on_chain(program, wallet, hash_bytes, log_url)
    
    if tx:
        print(f"  �� NFT minted!")
        
        # Save mapping
        mapping = {
            "filename": filename,
            "log_url": log_url,
            "hash": file_hash,
            "nft_tx": tx,
            "timestamp": int(time.time())
        }
        
        # Write to project root
        mappings_file = Path(__file__).parent.parent / "nft_mappings.json"
        mappings = []
        if mappings_file.exists():
            try:
                with open(mappings_file) as f:
                    content = f.read().strip()
                    if content:
                        mappings = json.loads(content)
            except:
                mappings = []
        
        mappings.append(mapping)
        
        with open(mappings_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        
        print(f"  ✓ Saved to {mappings_file}")
        
        return True
    else:
        print("  [ERROR] NFT minting failed")
        return False

async def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Complete Auto Mint Monitor - Upload & Mint NFTs       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Setup Solana connection
    client = AsyncClient(SOLANA_RPC, commitment=Confirmed)
    
    # Load wallet
    print(f"[INFO] Loading wallet: {WALLET_PATH}")
    with open(WALLET_PATH) as f:
        keypair = Keypair.from_bytes(json.load(f))
    wallet = Wallet(keypair)
    pubkey_str = str(wallet.public_key)
    
    print(f"[INFO] Wallet: {pubkey_str}")
    print(f"[INFO] Monitoring: {CONTRACT_DATA_DIR}")
    print(f"[INFO] Log Server: {LOG_SERVER_URL}")
    print(f"[INFO] Check interval: {CHECK_INTERVAL}s")
    print(f"[INFO] File age threshold: {FILE_AGE_MINUTES} minutes")
    print()
    
    # Create provider
    provider = Provider(client, wallet)
    
    # Load IDL
    idl_path = Path(SENTINEL_DIR) / "target" / "idl" / "sentinel.json"
    print(f"[INFO] Loading IDL: {idl_path}")
    with open(idl_path) as f:
        idl = Idl.from_json(json.dumps(json.load(f)))
    
    program = Program(idl, PROGRAM_ID, provider)
    
    # Check peer status
    peer_pda, _ = Pubkey.find_program_address(
        [b"peer", bytes(wallet.public_key)],
        PROGRAM_ID
    )
    
    try:
        peer_account = await program.account["PeerState"].fetch(peer_pda)
        if not peer_account.active:
            print("[ERROR] Wallet is not an active peer!")
            print("        Run: cd sentinel && python3 mint_nft.py")
            await client.close()
            return 1
        print(f"[INFO] Peer active (Karma: {peer_account.karma})")
    except:
        print("[ERROR] Wallet is not a network member!")
        print("        Run: cd sentinel && python3 mint_nft.py")
        await client.close()
        return 1
    
    print()
    print("[INFO] Burst Protection Settings:")
    print(f"       Overburst Duration: {OVERBURST_DURATION}s")
    print(f"       Burst Cooldown: {BURST_COOLDOWN}s")
    print(f"       Burst Duration: {BURST_DURATION}s")
    print(f"       Burst Threshold: {BURST_THRESHOLD} files")
    print()
    print("[INFO] Starting monitor...")
    print()
    
    processed = set()
    mint_timestamps = []  # Track mint times for burst detection
    in_cooldown = False
    cooldown_until = 0
    
    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_time = time.time()
            
            # Check if in cooldown
            if in_cooldown:
                if current_time < cooldown_until:
                    remaining = int(cooldown_until - current_time)
                    print(f"[{ts}] 🛑 COOLDOWN - {remaining}s remaining...")
                    await asyncio.sleep(min(5, remaining))
                    continue
                else:
                    in_cooldown = False
                    print(f"[{ts}] ✅ Cooldown ended, resuming...")
            
            print(f"[{ts}] Scanning...")
            
            log_dir = Path(CONTRACT_DATA_DIR)
            if not log_dir.exists():
                print(f"[WARN] Directory not found: {CONTRACT_DATA_DIR}")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            
            # Get all .log files
            log_files = sorted(log_dir.glob("*.log"))
            new_files = [f for f in log_files if str(f) not in processed]
            
            if not new_files:
                print("[INFO] No new files")
            else:
                print(f"[INFO] Found {len(new_files)} new file(s)")
                
                # Clean old timestamps (outside overburst window)
                mint_timestamps = [t for t in mint_timestamps if current_time - t < OVERBURST_DURATION]
                
                for f in new_files:
                    # Check burst protection before processing
                    recent_mints = [t for t in mint_timestamps if current_time - t < BURST_DURATION]
                    
                    if len(recent_mints) >= BURST_THRESHOLD:
                        print(f"[BURST] ⚠️  Burst detected! {len(recent_mints)} mints in {BURST_DURATION}s")
                        print(f"[BURST] Entering cooldown for {BURST_COOLDOWN}s...")
                        in_cooldown = True
                        cooldown_until = current_time + BURST_COOLDOWN
                        break
                    
                    # Process file
                    success = await process_file(str(f), program, wallet, pubkey_str)
                    processed.add(str(f))
                    
                    if success:
                        mint_timestamps.append(time.time())
                        print(f"[SUCCESS] Processed {f.name}")
                        print(f"[STATS] Mints in last {BURST_DURATION}s: {len([t for t in mint_timestamps if time.time() - t < BURST_DURATION])}")
                        print(f"[STATS] Mints in last {OVERBURST_DURATION}s: {len(mint_timestamps)}")
                    
                    # Delay between mints
                    await asyncio.sleep(MINT_DELAY)
            
            if not in_cooldown:
                print(f"\n[INFO] Next check in {CHECK_INTERVAL}s...")
                await asyncio.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopped by user")
    finally:
        await client.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
