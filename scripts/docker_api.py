#!/usr/bin/env python3
"""
Docker Management API for SentinelKarma
Control and monitor Docker services programmatically
"""

import subprocess
import json
import time
from typing import List, Dict, Optional, Any
from pathlib import Path


class DockerManagerAPI:
    """Docker Manager API for SentinelKarma services"""
    
    def __init__(self, project_dir: str = "/home/water/SentinelKarma"):
        """
        Initialize Docker Manager API
        
        Args:
            project_dir: Path to SentinelKarma project
        """
        self.project_dir = Path(project_dir)
        self.manager_script = self.project_dir / "manager.sh"
        
        # Service names
        self.services = [
            "mosquitto",
            "agent", 
            "generator",
            "saver",
            "log-server"
        ]
    
    def _run_command(self, cmd: List[str], cwd: str = None) -> Dict:
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_dir,
                check=True
            )
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode
            }
    
    def _run_manager(self, flags: List[str]) -> Dict:
        """Run manager.sh with given flags"""
        cmd = ["bash", str(self.manager_script)] + flags
        return self._run_command(cmd)
    
    def _run_docker_compose(self, args: List[str]) -> Dict:
        """Run docker compose command"""
        cmd = ["docker", "compose"] + args
        return self._run_command(cmd)
    
    def check_dependencies(self) -> Dict:
        """Check if all dependencies are installed"""
        result = self._run_manager(["--check"])
        return {
            "all_present": result["success"],
            "output": result["stdout"]
        }
    
    def install_dependencies(self) -> bool:
        """Install required dependencies"""
        result = self._run_manager(["--install"])
        return result["success"]
    
    def setup_docker(self) -> bool:
        """Setup Docker and build images"""
        result = self._run_manager(["--docker"])
        return result["success"]
    
    def start_services(self, services: List[str] = None) -> bool:
        """
        Start specific services or all
        
        Args:
            services: List of service names (default: all)
        """
        if services is None:
            result = self._run_docker_compose(["up", "-d"])
        else:
            result = self._run_docker_compose(["up", "-d"] + services)
        return result["success"]
    
    def stop_services(self, services: List[str] = None) -> bool:
        """
        Stop specific services or all
        
        Args:
            services: List of service names (default: all)
        """
        if services is None:
            result = self._run_manager(["--stop"])
        else:
            result = self._run_docker_compose(["stop"] + services)
        return result["success"]
    
    def restart_service(self, service: str) -> bool:
        """Restart a specific service"""
        result = self._run_docker_compose(["restart", service])
        return result["success"]
    
    def get_service_status(self, service: str = None) -> Dict:
        """
        Get status of service(s)
        
        Args:
            service: Service name (default: all)
        """
        if service:
            result = self._run_docker_compose(["ps", service])
        else:
            result = self._run_docker_compose(["ps"])
        
        if result["success"]:
            # Parse output
            lines = result["stdout"].strip().split('\n')
            services = {}
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[0]
                        status = "running" if "Up" in line else "stopped"
                        services[name] = status
            
            return services
        return {}
    
    def get_logs(self, service: str, lines: int = 100) -> str:
        """
        Get logs from a service
        
        Args:
            service: Service name
            lines: Number of lines to return
        """
        result = self._run_docker_compose(["logs", "--tail", str(lines), service])
        return result["stdout"] if result["success"] else ""
    
    def monitor_start(self, full: bool = False, verbose: bool = False, mute: bool = False) -> Dict:
        """
        Start monitoring
        
        Args:
            full: Enable full mode (auto-mint)
            verbose: Show all telemetry
            mute: Run in background
        """
        flags = ["--monitor"]
        if full:
            flags.append("--full")
        if verbose:
            flags.append("--verbose")
        if mute:
            flags.append("--mute")
        
        result = self._run_manager(flags)
        return result
    
    def test_mode(self) -> bool:
        """Start test mode with collectors"""
        result = self._run_manager(["--test"])
        return result["success"]
    
    def overburst(self, methods: List[str] = None, rate: int = 2000) -> bool:
        """
        Run overburst test
        
        Args:
            methods: RPC methods to burst
            rate: Request rate
        """
        import os
        env = os.environ.copy()
        
        if methods:
            env["OVER_METHODS"] = " ".join(methods)
        env["OVER_RATE"] = str(rate)
        
        cmd = ["bash", str(self.manager_script), "--overburst"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_dir,
            env=env
        )
        return result.returncode == 0
    
    def build_images(self) -> bool:
        """Rebuild Docker images"""
        result = self._run_docker_compose(["build"])
        return result["success"]
    
    def purge_project(self) -> bool:
        """Purge all project containers and images"""
        result = self._run_manager(["--docker-purge"])
        return result["success"]
    
    def exec_command(self, service: str, command: str) -> Dict:
        """
        Execute command in a service container
        
        Args:
            service: Service name
            command: Command to execute
        """
        result = self._run_docker_compose(["exec", "-T", service, "sh", "-c", command])
        return result
    
    def health_check(self) -> Dict:
        """Check health of all services"""
        health = {}
        
        # Check each service
        status = self.get_service_status()
        for service in self.services:
            health[service] = {
                "status": status.get(f"sentinelkarma-{service}-1", "unknown")
            }
        
        # Special health checks
        import requests
        
        # Log server health
        try:
            response = requests.get("http://localhost:9000/health", timeout=2)
            if response.status_code == 200:
                health["log-server"]["api"] = "healthy"
                health["log-server"]["details"] = response.json()
        except:
            health["log-server"]["api"] = "unreachable"
        
        # Mosquitto health
        result = self.exec_command("mosquitto", "mosquitto_sub -h localhost -t '$SYS/#' -C 1")
        health["mosquitto"]["mqtt"] = "healthy" if result["success"] else "unhealthy"
        
        return health
    
    def get_stats(self) -> Dict:
        """Get statistics from all services"""
        stats = {}
        
        # Docker stats
        result = self._run_docker_compose(["stats", "--no-stream"])
        if result["success"]:
            stats["docker"] = result["stdout"]
        
        # Log server stats
        try:
            import requests
            response = requests.get("http://localhost:9000/stats", timeout=2)
            if response.status_code == 200:
                stats["log_server"] = response.json()
        except:
            pass
        
        # Data directory stats
        data_dir = self.project_dir / "data"
        if data_dir.exists():
            stats["data"] = {
                "contract_data": len(list((data_dir / "contract_data").glob("*.log"))) if (data_dir / "contract_data").exists() else 0,
                "malicious_logs": len(list((data_dir / "malicious_logs").glob("*.jsonl"))) if (data_dir / "malicious_logs").exists() else 0,
                "logs_normal": len(list((data_dir / "logs_normal").glob("*.jsonl"))) if (data_dir / "logs_normal").exists() else 0,
            }
        
        return stats


# Example usage
if __name__ == "__main__":
    # Initialize API
    docker = DockerManagerAPI()
    
    print("Docker Manager API Examples")
    print("=" * 60)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    deps = docker.check_dependencies()
    print(f"   Dependencies OK: {deps['all_present']}")
    
    # Get service status
    print("\n2. Service Status:")
    status = docker.get_service_status()
    for service, state in status.items():
        print(f"   {service}: {state}")
    
    # Health check
    print("\n3. Health Check:")
    health = docker.health_check()
    for service, info in health.items():
        print(f"   {service}: {info.get('status', 'unknown')}")
    
    # Get stats
    print("\n4. Statistics:")
    stats = docker.get_stats()
    if "data" in stats:
        print(f"   Contract data files: {stats['data']['contract_data']}")
        print(f"   Malicious logs: {stats['data']['malicious_logs']}")
        print(f"   Normal logs: {stats['data']['logs_normal']}")
    
    print("\n" + "=" * 60)
    print("Quick Usage:")
    print("""
from docker_api import DockerManagerAPI

# Initialize
docker = DockerManagerAPI()

# Start services
docker.start_services()

# Start monitoring (full mode)
docker.monitor_start(full=True)

# Get logs
logs = docker.get_logs("agent", lines=50)

# Restart a service
docker.restart_service("log-server")

# Check health
health = docker.health_check()
    """)