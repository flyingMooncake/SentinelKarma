#!/usr/bin/env python3
"""
Example usage of SentinelKarma API
"""

import json
from sentinel_api import SentinelKarmaAPI, LogServerAPI, SentinelContractAPI

def example_log_server():
    """Example: Using Log Server API"""
    print("=" * 60)
    print("LOG SERVER API EXAMPLES")
    print("=" * 60)
    
    # Initialize API (auto-detects IP)
    api = LogServerAPI()
    print(f"Server URL: {api.server_url}")
    
    # Check health
    health = api.health()
    print(f"\nHealth: {json.dumps(health, indent=2)}")
    
    # Get stats
    stats = api.stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")
    
    # List existing logs
    logs = api.list_logs()
    print(f"\nFound {len(logs)} logs:")
    for log in logs:
        print(f"  - {log['log_id']}: {log['filename']}")
    
    # Upload a test file (if you have one)
    # result = api.upload_log("data/contract_data/test.log")
    # print(f"Upload result: {result}")


def example_contract():
    """Example: Using Contract API"""
    print("\n" + "=" * 60)
    print("CONTRACT API EXAMPLES")
    print("=" * 60)
    
    # Initialize API
    api = SentinelContractAPI()
    print(f"RPC URL: {api.rpc_url}")
    print(f"Program ID: {api.program_id}")
    print(f"Pubkey: {api.pubkey}")
    
    # Check balance
    balance = api.get_balance()
    print(f"\nBalance: {balance} SOL")
    
    # Request airdrop (testnet only)
    if balance < 1:
        print("Requesting airdrop...")
        if api.airdrop(10):
            print("✓ Airdrop successful")
        else:
            print("✗ Airdrop failed")
    
    # Create NFT mint
    # mint = api.create_nft_mint()
    # print(f"Created NFT mint: {mint}")


def example_combined():
    """Example: Using Combined API"""
    print("\n" + "=" * 60)
    print("COMBINED API EXAMPLE")
    print("=" * 60)
    
    # Initialize combined API
    api = SentinelKarmaAPI()
    
    # Get complete system status
    status = api.status()
    print(f"System Status:")
    print(f"  IP: {status['ip']}")
    print(f"  Log Server: {status['log_server']['url']}")
    print(f"  Contract RPC: {status['contract']['rpc']}")
    print(f"  Balance: {status['contract']['balance']} SOL")
    
    # Process a log file (upload + mint)
    # result = api.process_log_file("data/contract_data/test.log")
    # print(f"Processing result: {json.dumps(result, indent=2)}")


def example_batch_processing():
    """Example: Batch process multiple files"""
    print("\n" + "=" * 60)
    print("BATCH PROCESSING EXAMPLE")
    print("=" * 60)
    
    from pathlib import Path
    
    api = SentinelKarmaAPI()
    log_dir = Path("data/contract_data")
    
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        print(f"Found {len(log_files)} log files")
        
        for log_file in log_files[:3]:  # Process first 3
            print(f"\nProcessing: {log_file.name}")
            
            # Check if already uploaded
            file_hash = api.log_server._compute_hash(str(log_file))
            if api.log_server.check_exists(file_hash):
                print("  ✓ Already uploaded")
            else:
                print("  → Uploading...")
                result = api.log_server.upload_log(str(log_file))
                if "error" not in result:
                    print(f"  ✓ Uploaded: {result['log_id']}")
                else:
                    print(f"  ✗ Failed: {result['error']}")


if __name__ == "__main__":
    # Run examples
    example_log_server()
    example_contract()
    example_combined()
    example_batch_processing()
    
    print("\n" + "=" * 60)
    print("QUICK USAGE:")
    print("=" * 60)
    print("""
from sentinel_api import SentinelKarmaAPI

# Initialize
api = SentinelKarmaAPI()

# Upload a log
result = api.log_server.upload_log("path/to/file.log")

# Check if file exists
exists = api.log_server.check_exists(file_hash)

# Get balance
balance = api.contract.get_balance()

# Process file (upload + mint)
result = api.process_log_file("path/to/file.log")
    """)