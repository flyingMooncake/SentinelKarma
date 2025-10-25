#!/usr/bin/env python3
"""
SentinelKarma API Library
Provides easy-to-use interfaces for both HTTP log server and Solana contract
"""

import os
import json
import time
import hashlib
import requests
import subprocess
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime


class LogServerAPI:
    """HTTP Log Server API Client"""
    
    def __init__(self, server_url: str = None, pubkey: str = None, keypair_path: str = None):
        """
        Initialize Log Server API
        
        Args:
            server_url: Log server URL (default: auto-detect IP)
            pubkey: Solana public key (optional, will derive from keypair)
            keypair_path: Path to Solana keypair JSON
        """
        # Auto-detect IP if not provided
        if server_url is None:
            ip = self._get_wsl_ip()
            server_url = f"http://{ip}:9000"
        
        self.server_url = server_url.rstrip('/')
        
        # Get pubkey from keypair if not provided
        if pubkey is None and keypair_path:
            pubkey = self._get_pubkey_from_keypair(keypair_path)
        
        self.pubkey = pubkey or "FKYCbhJfA4K5rVqFdunr55LXT6Qo5kbG5uxEPGkW1iCc"
        self.keypair_path = keypair_path
    
    def _get_wsl_ip(self) -> str:
        """Get WSL IP address"""
        try:
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True,
                text=True,
                check=True
            )
            ip = result.stdout.strip().split()[0]
            return ip
        except:
            return "172.19.12.161"  # Fallback
    
    def _get_pubkey_from_keypair(self, keypair_path: str) -> str:
        """Extract public key from keypair file"""
        try:
            result = subprocess.run(
                ["solana-keygen", "pubkey", keypair_path],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def _compute_hash(self, filepath: str) -> str:
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def health(self) -> Dict:
        """Check server health"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            return {"error": str(e)}
    
    def stats(self) -> Dict:
        """Get server statistics"""
        try:
            response = requests.get(f"{self.server_url}/stats", timeout=5)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            return {"error": str(e)}
    
    def upload_log(self, filepath: str, compute_hash: bool = True) -> Dict:
        """
        Upload a log file to the server
        
        Args:
            filepath: Path to log file
            compute_hash: Whether to compute and return file hash
            
        Returns:
            Dict with log_id, url, hash, size
        """
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
        
        filename = os.path.basename(filepath)
        timestamp = int(time.time())
        
        headers = {
            'X-Peer-Pubkey': self.pubkey,
            'X-Timestamp': str(timestamp),
            'X-Signature': 'test_signature',  # Testing mode
        }
        
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                response = requests.post(
                    f"{self.server_url}/logs",
                    headers=headers,
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                if compute_hash:
                    result['local_hash'] = self._compute_hash(filepath)
                return result
            else:
                return {
                    "error": f"Upload failed: {response.status_code}",
                    "detail": response.text
                }
        except Exception as e:
            return {"error": str(e)}
    
    def download_log(self, log_id: str, output_path: str = None) -> bool:
        """
        Download a log file from the server
        
        Args:
            log_id: Log ID to download
            output_path: Where to save (optional)
            
        Returns:
            True if successful
        """
        timestamp = int(time.time())
        headers = {
            'X-Peer-Pubkey': self.pubkey,
            'X-Timestamp': str(timestamp),
            'X-Signature': 'test_signature',
        }
        
        try:
            response = requests.get(
                f"{self.server_url}/logs/{log_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                return True
            return False
        except:
            return False
    
    def get_metadata(self, log_id: str) -> Dict:
        """Get log metadata"""
        try:
            response = requests.get(
                f"{self.server_url}/logs/{log_id}/metadata",
                timeout=5
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            return {"error": str(e)}
    
    def list_logs(self) -> List[Dict]:
        """List all available logs with metadata"""
        # Known log IDs (from previous uploads)
        known_ids = [
            'ed2336ded3a9213a',
            '76d2cac8a861f1b9',
            'e5fa5faa647ef4dc',
            '9c0847bcf2109be5',
            'e87c7c582c50b96a'
        ]
        
        logs = []
        for log_id in known_ids:
            metadata = self.get_metadata(log_id)
            if metadata and 'error' not in metadata:
                logs.append(metadata)
        
        return logs
    
    def check_exists(self, file_hash: str) -> bool:
        """Check if a file (by hash) already exists on server"""
        log_id = file_hash[:16]
        metadata = self.get_metadata(log_id)
        return metadata is not None and 'error' not in metadata


class SentinelContractAPI:
    """Sentinel Solana Contract API Client"""
    
    def __init__(self, rpc_url: str = None, keypair_path: str = None, program_id: str = None):
        """
        Initialize Sentinel Contract API
        
        Args:
            rpc_url: Solana RPC URL (default: auto-detect)
            keypair_path: Path to keypair JSON
            program_id: Sentinel program ID
        """
        # Auto-detect RPC
        if rpc_url is None:
            ip = self._get_wsl_ip()
            rpc_url = f"http://{ip}:8899"
        
        self.rpc_url = rpc_url
        self.keypair_path = keypair_path or "./sentinel/deploy-keypair.json"
        self.program_id = program_id or "Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V"
        
        # Get pubkey
        self.pubkey = self._get_pubkey()
    
    def _get_wsl_ip(self) -> str:
        """Get WSL IP address"""
        try:
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True,
                text=True,
                check=True
            )
            ip = result.stdout.strip().split()[0]
            return ip
        except:
            return "172.19.12.161"
    
    def _get_pubkey(self) -> str:
        """Get public key from keypair"""
        try:
            result = subprocess.run(
                ["solana-keygen", "pubkey", self.keypair_path],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def _run_solana_cmd(self, args: List[str]) -> Dict:
        """Run Solana CLI command"""
        try:
            cmd = ["solana"] + args + ["--url", self.rpc_url]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return {"success": True, "output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}
    
    def get_balance(self, address: str = None) -> float:
        """Get SOL balance"""
        address = address or self.pubkey
        result = self._run_solana_cmd(["balance", address])
        if result["success"]:
            try:
                return float(result["output"].split()[0])
            except:
                return 0.0
        return 0.0
    
    def airdrop(self, amount: int = 100, address: str = None) -> bool:
        """Request airdrop (testnet only)"""
        address = address or self.pubkey
        result = self._run_solana_cmd(["airdrop", str(amount), address])
        return result["success"]
    
    def create_nft_mint(self) -> Optional[str]:
        """Create a new NFT mint (0 decimals)"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            mint_keypair_path = f.name
        
        try:
            # Generate mint keypair
            subprocess.run(
                ["solana-keygen", "new", "--no-bip39-passphrase", 
                 "--outfile", mint_keypair_path, "--force"],
                capture_output=True,
                check=True
            )
            
            # Get mint pubkey
            result = subprocess.run(
                ["solana-keygen", "pubkey", mint_keypair_path],
                capture_output=True,
                text=True,
                check=True
            )
            mint_pubkey = result.stdout.strip()
            
            # Create token mint
            subprocess.run(
                ["spl-token", "create-token", 
                 "--decimals", "0",
                 "--url", self.rpc_url,
                 mint_keypair_path],
                capture_output=True,
                check=True
            )
            
            return mint_pubkey
            
        except Exception as e:
            print(f"Error creating NFT mint: {e}")
            return None
        finally:
            if os.path.exists(mint_keypair_path):
                os.unlink(mint_keypair_path)
    
    def mint_nft(self, log_url: str, file_hash: str, mint_address: str = None) -> Dict:
        """
        Mint an NFT for a log file
        
        Args:
            log_url: URL to the log file
            file_hash: SHA256 hash of the file
            mint_address: Optional existing mint address
            
        Returns:
            Dict with transaction details
        """
        # Create mint if not provided
        if mint_address is None:
            mint_address = self.create_nft_mint()
            if not mint_address:
                return {"error": "Failed to create NFT mint"}
        
        # TODO: Implement actual Anchor transaction
        # For now, return placeholder
        return {
            "status": "placeholder",
            "mint": mint_address,
            "log_url": log_url,
            "file_hash": file_hash,
            "message": "On-chain minting not yet implemented"
        }
    
    def get_peer_info(self, peer_address: str = None) -> Dict:
        """Get peer information from contract"""
        peer_address = peer_address or self.pubkey
        
        # TODO: Implement actual contract query
        return {
            "peer": peer_address,
            "reputation": 100,
            "posts_count": 0,
            "message": "Contract queries not yet implemented"
        }


class SentinelKarmaAPI:
    """Combined API for SentinelKarma system"""
    
    def __init__(self, keypair_path: str = None):
        """
        Initialize combined API
        
        Args:
            keypair_path: Path to Solana keypair
        """
        # Auto-detect IP
        self.ip = self._get_wsl_ip()
        
        # Initialize sub-APIs
        self.log_server = LogServerAPI(
            server_url=f"http://{self.ip}:9000",
            keypair_path=keypair_path
        )
        
        self.contract = SentinelContractAPI(
            rpc_url=f"http://{self.ip}:8899",
            keypair_path=keypair_path
        )
        
        self.keypair_path = keypair_path or "./sentinel/deploy-keypair.json"
    
    def _get_wsl_ip(self) -> str:
        """Get WSL IP address"""
        try:
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True,
                text=True,
                check=True
            )
            ip = result.stdout.strip().split()[0]
            return ip
        except:
            return "172.19.12.161"
    
    def process_log_file(self, filepath: str) -> Dict:
        """
        Complete flow: upload log and mint NFT
        
        Args:
            filepath: Path to log file
            
        Returns:
            Dict with complete processing results
        """
        result = {
            "file": filepath,
            "upload": None,
            "mint": None
        }
        
        # Upload to log server
        upload_result = self.log_server.upload_log(filepath)
        result["upload"] = upload_result
        
        if "error" in upload_result:
            return result
        
        # Mint NFT
        mint_result = self.contract.mint_nft(
            log_url=upload_result["url"],
            file_hash=upload_result["hash"]
        )
        result["mint"] = mint_result
        
        return result
    
    def status(self) -> Dict:
        """Get complete system status"""
        return {
            "ip": self.ip,
            "log_server": {
                "url": self.log_server.server_url,
                "health": self.log_server.health(),
                "stats": self.log_server.stats()
            },
            "contract": {
                "rpc": self.contract.rpc_url,
                "program_id": self.contract.program_id,
                "balance": self.contract.get_balance(),
                "pubkey": self.contract.pubkey
            }
        }


# Example usage
if __name__ == "__main__":
    # Initialize API
    api = SentinelKarmaAPI()
    
    # Check status
    print("System Status:")
    print(json.dumps(api.status(), indent=2))
    
    # List logs
    print("\nAvailable Logs:")
    for log in api.log_server.list_logs():
        print(f"  - {log['log_id']}: {log['filename']} ({log['size']} bytes)")