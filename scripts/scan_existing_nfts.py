#!/usr/bin/env python3
"""
Scan existing contract data files and check if they're already minted
Populate nft_mappings.json with existing NFTs
"""

import json
import os
from pathlib import Path

def main():
    print("Scanning for existing contract data files...")
    
    contract_dir = Path("./data/contract_data")
    if not contract_dir.exists():
        print("No contract_data directory found")
        return
    
    files = sorted(contract_dir.glob("cd_*.log"))
    print(f"Found {len(files)} contract data files")
    
    # Load existing mappings
    mappings_file = Path("./nft_mappings.json")
    mappings = []
    if mappings_file.exists():
        try:
            with open(mappings_file) as f:
                content = f.read().strip()
                if content:
                    mappings = json.loads(content)
        except:
            mappings = []
    
    print(f"Existing mappings: {len(mappings)}")
    
    # For now, just show what we have
    print("\nContract data files:")
    for f in files[:10]:  # Show first 10
        print(f"  - {f.name}")
    
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more")
    
    print(f"\nTo mint these files, run the auto-mint monitor")
    print("It will process recent files (< 60 minutes old)")

if __name__ == "__main__":
    main()
