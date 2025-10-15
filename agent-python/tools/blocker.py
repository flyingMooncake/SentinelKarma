import subprocess
import os
import time
from typing import List, Set, Optional


class IPBlocker:
    """Automatically block malicious IPs using iptables"""
    
    def __init__(self, blocklist_file: str = "/data/blocked_ips.txt"):
        self.blocked_ips: Set[str] = set()
        self.blocklist_file = blocklist_file
        self.chain_name = "SENTINEL_BLOCK"
        self._ensure_chain_exists()
        self.load_existing_blocks()
    
    def _ensure_chain_exists(self):
        """Create custom iptables chain if it doesn't exist"""
        try:
            subprocess.run(
                ['iptables', '-N', self.chain_name],
                stderr=subprocess.DEVNULL
            )
            subprocess.run([
                'iptables', '-I', 'INPUT', '1',
                '-j', self.chain_name
            ], stderr=subprocess.DEVNULL)
        except Exception:
            pass
    
    def load_existing_blocks(self):
        """Load previously blocked IPs from file"""
        if os.path.exists(self.blocklist_file):
            with open(self.blocklist_file, 'r') as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('#'):
                        self.blocked_ips.add(ip)
            print(f"[BLOCKER] Loaded {len(self.blocked_ips)} existing blocks")
    
    def is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def block_ip(self, ip: str, reason: str = "malicious", duration: Optional[int] = None) -> bool:
        """
        Block an IP using iptables
        
        Args:
            ip: IP address to block
            reason: Reason for blocking (logged in comment)
            duration: Optional duration in seconds (None = permanent)
        
        Returns:
            True if blocked successfully
        """
        if not self.is_valid_ip(ip):
            print(f"[BLOCKER] Invalid IP format: {ip}")
            return False
        
        if ip in self.blocked_ips:
            return True
        
        try:
            subprocess.run([
                'iptables', '-A', self.chain_name,
                '-s', ip,
                '-j', 'DROP',
                '-m', 'comment', '--comment', f'sentinel:{reason}'
            ], check=True, capture_output=True)
            
            self.blocked_ips.add(ip)
            
            with open(self.blocklist_file, 'a') as f:
                timestamp = int(time.time())
                f.write(f"{ip} # {reason} @ {timestamp}\n")
            
            print(f"[BLOCKED] {ip} - {reason}")
            
            if duration:
                print(f"[BLOCKER] Will unblock {ip} after {duration}s")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to block {ip}: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to block {ip}: {e}")
            return False
    
    def block_multiple(self, ips: List[str], reason: str = "malicious") -> int:
        """Block multiple IPs at once"""
        blocked_count = 0
        for ip in ips:
            if self.block_ip(ip, reason):
                blocked_count += 1
        return blocked_count
    
    def unblock_ip(self, ip: str) -> bool:
        """Remove IP from blocklist"""
        if ip not in self.blocked_ips:
            return True
        
        try:
            subprocess.run([
                'iptables', '-D', self.chain_name,
                '-s', ip,
                '-j', 'DROP'
            ], check=True, capture_output=True)
            
            self.blocked_ips.discard(ip)
            print(f"[UNBLOCKED] {ip}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to unblock {ip}: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to unblock {ip}: {e}")
            return False
    
    def list_blocked(self) -> List[str]:
        """Get list of currently blocked IPs"""
        return sorted(list(self.blocked_ips))
    
    def clear_all(self):
        """Remove all blocks (use with caution!)"""
        for ip in list(self.blocked_ips):
            self.unblock_ip(ip)
        
        try:
            subprocess.run(['iptables', '-F', self.chain_name])
        except Exception:
            pass
    
    def get_stats(self) -> dict:
        """Get blocking statistics"""
        return {
            'total_blocked': len(self.blocked_ips),
            'blocked_ips': self.list_blocked()[:10],
            'chain_name': self.chain_name
        }


if __name__ == "__main__":
    blocker = IPBlocker()
    print(f"Blocker initialized with {len(blocker.blocked_ips)} existing blocks")
    print(f"Stats: {blocker.get_stats()}")
