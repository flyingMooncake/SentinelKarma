#!/usr/bin/env python3
"""
Log Client - Upload and download logs from peer network
"""

import os
import time
import hashlib
import requests
from typing import Optional
from solders.keypair import Keypair


class LogClient:
    """Client for uploading and downloading logs from peer network"""
    
    def __init__(self, keypair: Keypair, my_server_url: Optional[str] = None):
        self.keypair = keypair
        self.pubkey = str(keypair.pubkey())
        self.my_server_url = my_server_url or os.getenv("MY_PEER_URL", "http://localhost:9000")
    
    def _sign_message(self, message: str) -> str:
        """Sign a message with peer's private key"""
        signature = self.keypair.sign_message(message.encode())
        return str(signature)
    
    def upload_log(self, log_path: str) -> tuple[str, str]:
        """
        Upload log to own server
        
        Returns:
            (log_url, file_hash)
        """
        # Read log file
        with open(log_path, 'rb') as f:
            content = f.read()
        
        # Compute hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Prepare request
        timestamp = int(time.time())
        filename = os.path.basename(log_path)
        
        # Sign
        message = f"{filename}{timestamp}{self.pubkey}"
        signature = self._sign_message(message)
        
        # Upload to own server
        files = {'file': (filename, content)}
        headers = {
            'X-Peer-Pubkey': self.pubkey,
            'X-Timestamp': str(timestamp),
            'X-Signature': signature
        }
        
        response = requests.post(
            f"{self.my_server_url}/logs",
            files=files,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
        
        data = response.json()
        return data['url'], data['hash']
    
    def download_log(self, log_url: str, expected_hash: str) -> bytes:
        """
        Download and verify log from peer
        
        Args:
            log_url: Full URL to log (e.g., "https://peer.com:9000/logs/abc123")
            expected_hash: Expected SHA256 hash from blockchain
        
        Returns:
            Log content as bytes
        
        Raises:
            Exception if download fails or hash doesn't match
        """
        # Extract log_id from URL
        log_id = log_url.split('/logs/')[-1]
        
        # Prepare signed request
        timestamp = int(time.time())
        message = f"{log_id}{timestamp}{self.pubkey}"
        signature = self._sign_message(message)
        
        # Request log
        headers = {
            'X-Peer-Pubkey': self.pubkey,
            'X-Timestamp': str(timestamp),
            'X-Signature': signature
        }
        
        response = requests.get(
            log_url,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 403:
            raise Exception("Access denied - not authorized")
        elif response.status_code == 404:
            raise Exception("Log not found")
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded")
        elif response.status_code != 200:
            raise Exception(f"Download failed: {response.status_code}")
        
        # Verify hash
        content = response.content
        actual_hash = hashlib.sha256(content).hexdigest()
        
        if actual_hash != expected_hash:
            raise Exception(f"Hash mismatch! Expected {expected_hash}, got {actual_hash}")
        
        return content
    
    def get_metadata(self, log_url: str) -> dict:
        """Get log metadata (no auth required)"""
        metadata_url = log_url + "/metadata"
        response = requests.get(metadata_url, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get metadata: {response.status_code}")
        
        return response.json()


def example_usage():
    """Example: Upload and download logs"""
    
    # Load keypair
    keypair = Keypair()  # In production, load from secure storage
    
    # Initialize client
    client = LogClient(
        keypair=keypair,
        my_server_url="http://localhost:9000"
    )
    
    # Upload log
    print("Uploading log...")
    log_url, file_hash = client.upload_log("/data/malicious_logs/attack.log")
    print(f"Uploaded: {log_url}")
    print(f"Hash: {file_hash}")
    
    # Download log (from another peer)
    print("\nDownloading log from peer...")
    peer_url = "http://peer-a.com:9000/logs/abc123"
    expected_hash = "1234567890abcdef..."
    
    try:
        content = client.download_log(peer_url, expected_hash)
        print(f"Downloaded {len(content)} bytes")
        print("Hash verified ✓")
    except Exception as e:
        print(f"Download failed: {e}")


if __name__ == "__main__":
    example_usage()
