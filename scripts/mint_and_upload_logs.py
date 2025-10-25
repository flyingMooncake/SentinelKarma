#!/usr/bin/env python3
"""
Mint NFTs for all contract data logs and upload them to the HTTP log server
1. Reads all .log files from data/contract_data/
2. Computes SHA256 hash for each file
3. Uploads to HTTP log server (localhost:9000)
4. Mints NFT on Sentinel contract with log URL and hash
"""

import os
import sys
import json
import hashlib
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional

# Configuration
RPC_URL = os.getenv("RPC_URL", "http://localhost:8899")
KEYPAIR_PATH = os.getenv("KEYPAIR_PATH", "./sentinel/deploy-keypair.json")
CONTRACT_DATA_DIR = os.getenv("CONTRACT_DATA_DIR", "./data/contract_data")
LOG_SERVER_URL = os.getenv("LOG_SERVER_URL", "http://localhost:9000")
PROGRAM_ID = "Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V"

# For testing - allow all downloads (no signature verification)
ALLOW_ALL_DOWNLOADS = True


def load_keypair(path: str) -> Dict:
    """Load keypair from JSON file"""
    with open(path, 'r') as f:
        return json.load(f)


def get_pubkey_from_keypair(keypair: List[int]) -> str:
    """Get public key from keypair bytes (simplified)"""
    try:
        from solders.keypair import Keypair
        kp = Keypair.from_bytes(bytes(keypair))
        return str(kp.pubkey())
    except ImportError:
        # Fallback: use solana CLI
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(keypair, f)
            temp_path = f.name
        
        import subprocess
        result = subprocess.run(
            ['solana-keygen', 'pubkey', temp_path],
            capture_output=True,
            text=True
        )
        os.unlink(temp_path)
        return result.stdout.strip()


def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_log_files(directory: str) -> List[str]:
    """Get all log files from directory"""
    log_dir = Path(directory)
    if not log_dir.exists():
        print(f"[ERROR] Directory not found: {directory}")
        return []
    
    log_files = sorted(log_dir.glob("*.log"))
    return [str(f) for f in log_files]


def upload_to_log_server(
    filepath: str,
    pubkey: str,
    server_url: str
) -> Optional[Dict]:
    """Upload log file to HTTP log server"""
    
    filename = os.path.basename(filepath)
    
    # For testing: no signature verification
    # In production, you'd sign: sign(filename + timestamp + pubkey)
    timestamp = int(time.time())
    signature = "test_signature_allow_all"  # Placeholder
    
    headers = {
        'X-Peer-Pubkey': pubkey,
        'X-Timestamp': str(timestamp),
        'X-Signature': signature,
    }
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            
            response = requests.post(
                f"{server_url}/logs",
                headers=headers,
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  [ERROR] Upload failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"  [ERROR] Upload exception: {e}")
        return None


def create_nft_mint(pubkey: str, rpc_url: str) -> Optional[str]:
    """Create a new NFT mint using Solana CLI"""
    import subprocess
    import tempfile
    
    # Generate new keypair for the mint
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        mint_keypair_path = f.name
    
    try:
        # Generate mint keypair
        result = subprocess.run(
            ['solana-keygen', 'new', '--no-bip39-passphrase', '--outfile', mint_keypair_path, '--force'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  [ERROR] Failed to generate mint keypair: {result.stderr}")
            return None
        
        # Get mint pubkey
        result = subprocess.run(
            ['solana-keygen', 'pubkey', mint_keypair_path],
            capture_output=True,
            text=True
        )
        mint_pubkey = result.stdout.strip()
        
        # Create mint account using spl-token
        result = subprocess.run(
            [
                'spl-token', 'create-token',
                '--decimals', '0',  # NFT = 0 decimals
                '--url', rpc_url,
                mint_keypair_path
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  [ERROR] Failed to create token: {result.stderr}")
            return None
        
        print(f"  ✓ NFT mint created: {mint_pubkey}")
        return mint_pubkey
        
    finally:
        if os.path.exists(mint_keypair_path):
            os.unlink(mint_keypair_path)


def mint_nft_on_chain(
    keypair_path: str,
    mint_pubkey: str,
    log_url: str,
    file_hash: str,
    rpc_url: str
) -> bool:
    """
    Mint NFT on Sentinel contract
    Note: This is a placeholder - you'll need to implement the actual Anchor call
    """
    
    print(f"  [INFO] Would call Sentinel.mint_nft():")
    print(f"    mint: {mint_pubkey}")
    print(f"    url: {log_url}")
    print(f"    hash: {file_hash}")
    
    # TODO: Implement actual Anchor transaction
    # For now, just simulate success
    print(f"  [WARN] Skipping on-chain mint (not implemented yet)")
    print(f"  [INFO] To implement: use anchor-py or build transaction manually")
    
    return True


def process_log_file(
    log_file: str,
    keypair_path: str,
    pubkey: str,
    server_url: str,
    rpc_url: str
) -> bool:
    """Process a single log file: upload and mint NFT"""
    
    filename = os.path.basename(log_file)
    print(f"\n{'='*60}")
    print(f"Processing: {filename}")
    print(f"{'='*60}")
    
    # Step 1: Compute file hash
    print(f"[1/4] Computing file hash...")
    file_hash = compute_file_hash(log_file)
    file_size = os.path.getsize(log_file)
    print(f"  Hash: {file_hash}")
    print(f"  Size: {file_size} bytes")
    
    # Step 2: Upload to log server
    print(f"[2/4] Uploading to log server...")
    upload_result = upload_to_log_server(log_file, pubkey, server_url)
    
    if not upload_result:
        print(f"  [ERROR] Upload failed!")
        return False
    
    log_id = upload_result.get('log_id')
    log_url = upload_result.get('url')
    server_hash = upload_result.get('hash')
    
    print(f"  ✓ Uploaded successfully!")
    print(f"    Log ID: {log_id}")
    print(f"    URL: {log_url}")
    
    # Verify hash matches
    if server_hash != file_hash:
        print(f"  [ERROR] Hash mismatch!")
        print(f"    Local:  {file_hash}")
        print(f"    Server: {server_hash}")
        return False
    
    print(f"  ✓ Hash verified!")
    
    # Step 3: Create NFT mint
    print(f"[3/4] Creating NFT mint...")
    mint_pubkey = create_nft_mint(pubkey, rpc_url)
    
    if not mint_pubkey:
        print(f"  [ERROR] Failed to create NFT mint!")
        return False
    
    # Step 4: Mint NFT on Sentinel contract
    print(f"[4/4] Minting NFT on Sentinel contract...")
    if not mint_nft_on_chain(keypair_path, mint_pubkey, log_url, file_hash, rpc_url):
        print(f"  [ERROR] Failed to mint NFT on-chain!")
        return False
    
    print(f"\n✓ Successfully processed {filename}")
    print(f"  NFT Mint: {mint_pubkey}")
    print(f"  Log URL: {log_url}")
    
    return True


def check_log_server(server_url: str) -> bool:
    """Check if log server is running"""
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[INFO] Log server status: {data.get('status')}")
            print(f"  Logs stored: {data.get('logs_stored')}")
            print(f"  Storage used: {data.get('storage_used_mb')} MB")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Log server not responding: {e}")
        return False


def check_solana_rpc(rpc_url: str) -> bool:
    """Check if Solana RPC is responding"""
    try:
        response = requests.post(
            rpc_url,
            json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Solana RPC not responding: {e}")
        return False


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Mint NFTs and Upload Contract Data Logs               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Load keypair
    print(f"[INFO] Loading keypair from: {KEYPAIR_PATH}")
    try:
        keypair = load_keypair(KEYPAIR_PATH)
        pubkey = get_pubkey_from_keypair(keypair)
        print(f"[INFO] Payer: {pubkey}")
    except Exception as e:
        print(f"[ERROR] Failed to load keypair: {e}")
        return 1
    
    # Check log server
    print(f"\n[INFO] Checking log server: {LOG_SERVER_URL}")
    if not check_log_server(LOG_SERVER_URL):
        print(f"[ERROR] Log server is not running!")
        print(f"Start it with: ./manager.sh --monitor")
        return 1
    
    # Check Solana RPC
    print(f"\n[INFO] Checking Solana RPC: {RPC_URL}")
    if not check_solana_rpc(RPC_URL):
        print(f"[ERROR] Solana RPC is not responding!")
        print(f"Start testnet with: cd solanaTestNetDocker && ./manager.sh --validate")
        return 1
    
    # Get log files
    print(f"\n[INFO] Scanning directory: {CONTRACT_DATA_DIR}")
    log_files = get_log_files(CONTRACT_DATA_DIR)
    
    if not log_files:
        print("[ERROR] No log files found!")
        return 1
    
    print(f"[INFO] Found {len(log_files)} log files:")
    for i, log_file in enumerate(log_files, 1):
        print(f"  [{i}] {os.path.basename(log_file)}")
    
    # Confirm
    print(f"\n[WARN] This will:")
    print(f"  1. Upload {len(log_files)} files to {LOG_SERVER_URL}")
    print(f"  2. Create {len(log_files)} NFT mints")
    print(f"  3. Mint {len(log_files)} NFTs on Sentinel contract")
    
    if ALLOW_ALL_DOWNLOADS:
        print(f"\n[WARN] TESTING MODE: All downloads allowed (no signature verification)")
    
    response = input(f"\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return 0
    
    # Process each log file
    print(f"\n{'='*60}")
    print("Starting processing...")
    print(f"{'='*60}")
    
    success_count = 0
    fail_count = 0
    results = []
    
    for log_file in log_files:
        try:
            if process_log_file(log_file, KEYPAIR_PATH, pubkey, LOG_SERVER_URL, RPC_URL):
                success_count += 1
                results.append((os.path.basename(log_file), "SUCCESS"))
            else:
                fail_count += 1
                results.append((os.path.basename(log_file), "FAILED"))
        except KeyboardInterrupt:
            print("\n\n[WARN] Interrupted by user")
            break
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            fail_count += 1
            results.append((os.path.basename(log_file), f"ERROR: {e}"))
        
        # Small delay between files
        time.sleep(1)
    
    # Summary
    print(f"\n{'='*60}")
    print("Processing Summary")
    print(f"{'='*60}")
    print(f"Total files:    {len(log_files)}")
    print(f"Success:        {success_count}")
    print(f"Failed:         {fail_count}")
    print(f"{'='*60}")
    
    print("\nDetailed Results:")
    for filename, status in results:
        status_icon = "✓" if status == "SUCCESS" else "✗"
        print(f"  {status_icon} {filename}: {status}")
    
    print(f"\n{'='*60}")
    print("Next Steps:")
    print(f"{'='*60}")
    print(f"1. View uploaded logs: curl {LOG_SERVER_URL}/stats")
    print(f"2. Download a log: curl {LOG_SERVER_URL}/logs/<log_id>")
    print(f"3. Check log server: curl {LOG_SERVER_URL}/health")
    print(f"{'='*60}")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
