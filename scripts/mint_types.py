"""
Python types for Sentinel NFT minting
Matches the on-chain Post account structure
"""

from dataclasses import dataclass
from typing import List, Optional
import hashlib
import json


@dataclass
class MintNftInput:
    """Input data required for minting an NFT"""
    
    # HTTP URL to the log file (max 200 characters)
    log_url: str
    
    # SHA256 hash of the log file (64 hex characters)
    file_hash: str
    
    def validate(self) -> bool:
        """Validate the input data"""
        # Check URL length
        if len(self.log_url) > 200:
            raise ValueError("URL too long (max 200 characters)")
        
        # Check URL format
        if not (self.log_url.startswith("http://") or self.log_url.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        
        # Check hash format (64 hex chars = 32 bytes)
        if len(self.file_hash) != 64:
            raise ValueError("Hash must be 64 hex characters")
        
        try:
            int(self.file_hash, 16)
        except ValueError:
            raise ValueError("Hash must be valid hexadecimal")
        
        return True
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "log_url": self.log_url,
            "file_hash": self.file_hash
        })
    
    def get_hash_bytes(self) -> List[int]:
        """Get hash as list of bytes for on-chain storage"""
        return list(bytes.fromhex(self.file_hash))


@dataclass
class PostAccount:
    """On-chain Post account data structure"""
    
    # Owner's public key (32 bytes)
    owner: str
    
    # NFT mint address (32 bytes)
    nft_mint: str
    
    # HTTP URL to log file (max 200 chars)
    log_url: str
    
    # SHA256 hash of log file (32 bytes)
    file_hash: bytes
    
    # Number of likes
    likes: int
    
    # Cycle index when posted
    cycle_index: int
    
    @property
    def file_hash_hex(self) -> str:
        """Get file hash as hex string"""
        return self.file_hash.hex()


class MintDataBuilder:
    """Helper class to build mint data from log files"""
    
    @staticmethod
    def from_log_file(filepath: str, server_url: str, log_id: str) -> MintNftInput:
        """
        Create mint data from a log file
        
        Args:
            filepath: Path to the log file
            server_url: Base URL of log server (e.g., http://172.19.12.161:9000)
            log_id: Log ID on the server
        
        Returns:
            MintNftInput ready for minting
        """
        # Compute file hash
        file_hash = MintDataBuilder.compute_file_hash(filepath)
        
        # Build URL
        log_url = f"{server_url}/logs/{log_id}"
        
        return MintNftInput(
            log_url=log_url,
            file_hash=file_hash
        )
    
    @staticmethod
    def compute_file_hash(filepath: str) -> str:
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def from_upload_response(upload_response: dict, server_url: str = None) -> MintNftInput:
        """
        Create mint data from log server upload response
        
        Args:
            upload_response: Response from log server upload
            server_url: Optional override for server URL
        
        Returns:
            MintNftInput ready for minting
        """
        log_url = upload_response.get("url")
        if not log_url and server_url:
            log_url = f"{server_url}/logs/{upload_response['log_id']}"
        
        return MintNftInput(
            log_url=log_url,
            file_hash=upload_response["hash"]
        )


# Account sizes (in bytes)
ACCOUNT_SIZES = {
    "State": 112,       # 32 + 32 + 32 + 8 + 8
    "PeerState": 48,    # 32 + 1 + 8 + padding
    "Post": 320,        # 32 + 32 + (4 + 200) + 32 + 8 + 8
    "Like": 64,         # 32 + 32
    "TreasuryVault": 8  # minimal
}

# Example mint data
EXAMPLE_MINT_DATA = MintNftInput(
    log_url="http://172.19.12.161:9000/logs/ed2336ded3a9213a",
    file_hash="ed2336ded3a9213a3aa1f7a0a563527a5549d243b0970e482e257bc374b72cd6"
)


# Example usage
if __name__ == "__main__":
    # Create from upload response
    upload_response = {
        "log_id": "ed2336ded3a9213a",
        "url": "http://172.19.12.161:9000/logs/ed2336ded3a9213a",
        "hash": "ed2336ded3a9213a3aa1f7a0a563527a5549d243b0970e482e257bc374b72cd6",
        "size": 295
    }
    
    mint_data = MintDataBuilder.from_upload_response(upload_response)
    
    # Validate
    mint_data.validate()
    
    # Convert to JSON
    print("Mint Data JSON:")
    print(mint_data.to_json())
    
    # Get hash as bytes for on-chain
    hash_bytes = mint_data.get_hash_bytes()
    print(f"\nHash bytes (first 8): {hash_bytes[:8]}")
    
    # Show account sizes
    print("\nAccount Sizes:")
    for account, size in ACCOUNT_SIZES.items():
        print(f"  {account}: {size} bytes")