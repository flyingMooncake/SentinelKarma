#!/usr/bin/env python3
"""
Peer Log Server - Simple HTTP server for sharing malicious logs
Each peer runs this to serve their logs to other network members
"""

import os
import time
import hashlib
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="SentinelKarma Peer Log Server")

# Configuration
LOGS_DIR = os.getenv("LOGS_DIR", "/data/logs")
AUTHORIZED_PEERS_FILE = os.getenv("AUTHORIZED_PEERS_FILE", "/data/authorized_peers.txt")
MY_PEER_URL = os.getenv("MY_PEER_URL", "http://localhost:9000")
MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE", str(10 * 1024 * 1024)))  # 10MB
MAX_STORAGE = int(os.getenv("MAX_STORAGE", str(1024 * 1024 * 1024)))  # 1GB
TESTING_MODE = os.getenv("TESTING_MODE", "true").lower() == "true"  # Allow all for testing

# Authorized peers (synced from blockchain)
AUTHORIZED_PEERS = set()

# Bandwidth tracking (peer_pubkey -> bytes_sent)
bandwidth_usage = {}

os.makedirs(LOGS_DIR, exist_ok=True)


class UploadResponse(BaseModel):
    log_id: str
    url: str
    hash: str
    size: int


class TransferRequest(BaseModel):
    recipient: str
    amount: float


def load_authorized_peers():
    """Load authorized peers from file (synced from blockchain)"""
    if os.path.exists(AUTHORIZED_PEERS_FILE) and os.path.isfile(AUTHORIZED_PEERS_FILE):
        with open(AUTHORIZED_PEERS_FILE, 'r') as f:
            for line in f:
                pubkey = line.strip()
                if pubkey and not pubkey.startswith('#'):
                    AUTHORIZED_PEERS.add(pubkey)
        print(f"[SERVER] Loaded {len(AUTHORIZED_PEERS)} authorized peers")
    else:
        print(f"[SERVER] No authorized peers file found (testing mode enabled)")


def verify_signature(message: bytes, signature_str: str, pubkey_str: str) -> bool:
    """Verify Ed25519 signature (simplified for now)"""
    # TODO: Implement proper Ed25519 verification with solders
    return pubkey_str in AUTHORIZED_PEERS


def cleanup_old_logs():
    """Remove old logs if storage limit exceeded"""
    try:
        logs = []
        for filename in os.listdir(LOGS_DIR):
            if filename.endswith('.log'):
                path = os.path.join(LOGS_DIR, filename)
                logs.append((path, os.path.getmtime(path), os.path.getsize(path)))
        
        # Sort by modification time (oldest first)
        logs.sort(key=lambda x: x[1])
        
        total_size = sum(size for _, _, size in logs)
        
        # Remove oldest logs until under limit
        while total_size > MAX_STORAGE and logs:
            path, _, size = logs.pop(0)
            try:
                os.remove(path)
                # Remove metadata too
                meta_path = path.replace('.log', '.meta')
                if os.path.exists(meta_path):
                    os.remove(meta_path)
                total_size -= size
                print(f"[CLEANUP] Removed {path}")
            except Exception as e:
                print(f"[ERROR] Failed to remove {path}: {e}")
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {e}")


@app.on_event("startup")
async def startup():
    """Initialize server"""
    load_authorized_peers()
    cleanup_old_logs()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the download page"""
    index_path = os.path.join(LOGS_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return f.read()
    return "<h1>SentinelKarma Log Server</h1><p>No index.html found</p>"


@app.get("/health")
async def health():
    """Health check endpoint"""
    logs = [f for f in os.listdir(LOGS_DIR) if f.endswith('.log')]
    total_size = sum(os.path.getsize(os.path.join(LOGS_DIR, f)) for f in logs)
    
    return {
        "status": "healthy",
        "logs_stored": len(logs),
        "storage_used_mb": round(total_size / 1024 / 1024, 2),
        "storage_limit_mb": round(MAX_STORAGE / 1024 / 1024, 2),
        "authorized_peers": len(AUTHORIZED_PEERS),
        "my_url": MY_PEER_URL
    }


@app.post("/logs", response_model=UploadResponse)
async def upload_log(
    file: UploadFile = File(...),
    x_peer_pubkey: str = Header(...),
    x_timestamp: int = Header(...),
    x_signature: str = Header(...)
):
    """
    Upload a log file (usually called by own peer)
    
    Headers:
    - X-Peer-Pubkey: Your Solana public key
    - X-Timestamp: Current Unix timestamp
    - X-Signature: sign(filename + timestamp + pubkey)
    """
    # Skip auth in testing mode
    if not TESTING_MODE:
        # Verify timestamp is recent (within 5 minutes)
        now = int(time.time())
        if abs(now - x_timestamp) > 300:
            raise HTTPException(status_code=401, detail="Request expired")
        
        # Verify peer is authorized
        if x_peer_pubkey not in AUTHORIZED_PEERS:
            raise HTTPException(status_code=403, detail="Peer not authorized")
        
        # Verify signature
        message = f"{file.filename}{x_timestamp}{x_peer_pubkey}".encode()
        if not verify_signature(message, x_signature, x_peer_pubkey):
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        print(f"[TESTING] Skipping auth for upload from {x_peer_pubkey[:8]}...")
    
    # Read file content
    content = await file.read()
    
    # Check size limit
    if len(content) > MAX_LOG_SIZE:
        raise HTTPException(status_code=413, detail=f"Log too large (max {MAX_LOG_SIZE} bytes)")
    
    # Compute hash (use as log ID)
    file_hash = hashlib.sha256(content).hexdigest()
    log_id = file_hash[:16]  # Use first 16 chars as ID
    
    # Save to disk
    log_path = os.path.join(LOGS_DIR, f"{log_id}.log")
    with open(log_path, 'wb') as f:
        f.write(content)
    
    # Save metadata
    metadata = {
        'log_id': log_id,
        'filename': file.filename,
        'uploader': x_peer_pubkey,
        'timestamp': x_timestamp,
        'hash': file_hash,
        'size': len(content)
    }
    
    metadata_path = os.path.join(LOGS_DIR, f"{log_id}.meta")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    
    print(f"[UPLOAD] {log_id} by {x_peer_pubkey[:8]}... ({len(content)} bytes)")
    
    # Cleanup if needed
    cleanup_old_logs()
    
    return UploadResponse(
        log_id=log_id,
        url=f"{MY_PEER_URL}/logs/{log_id}",
        hash=file_hash,
        size=len(content)
    )


@app.get("/logs/{log_id}")
async def download_log(
    log_id: str,
    x_peer_pubkey: str = Header(...),
    x_timestamp: int = Header(...),
    x_signature: str = Header(...)
):
    """
    Download a log file
    
    Headers:
    - X-Peer-Pubkey: Your Solana public key
    - X-Timestamp: Current Unix timestamp
    - X-Signature: sign(log_id + timestamp + pubkey)
    """
    # Skip auth in testing mode
    if not TESTING_MODE:
        # Verify timestamp is recent
        now = int(time.time())
        if abs(now - x_timestamp) > 300:
            raise HTTPException(status_code=401, detail="Request expired")
        
        # Verify peer is authorized
        if x_peer_pubkey not in AUTHORIZED_PEERS:
            raise HTTPException(status_code=403, detail="Peer not authorized")
        
        # Verify signature
        message = f"{log_id}{x_timestamp}{x_peer_pubkey}".encode()
        if not verify_signature(message, x_signature, x_peer_pubkey):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Check bandwidth limit (100MB per day per peer)
        daily_limit = 100 * 1024 * 1024
        if bandwidth_usage.get(x_peer_pubkey, 0) > daily_limit:
            raise HTTPException(status_code=429, detail="Daily bandwidth limit exceeded")
    else:
        print(f"[TESTING] Skipping auth for download of {log_id} by {x_peer_pubkey[:8]}...")
    
    # Check if log exists
    log_path = os.path.join(LOGS_DIR, f"{log_id}.log")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Log not found")
    
    # Track bandwidth
    file_size = os.path.getsize(log_path)
    bandwidth_usage[x_peer_pubkey] = bandwidth_usage.get(x_peer_pubkey, 0) + file_size
    
    print(f"[DOWNLOAD] {log_id} by {x_peer_pubkey[:8]}... ({file_size} bytes)")
    
    return FileResponse(
        log_path,
        media_type="application/octet-stream",
        filename=f"{log_id}.log"
    )


@app.get("/logs/{log_id}/metadata")
async def get_metadata(log_id: str):
    """Get log metadata (public, no auth required)"""
    metadata_path = os.path.join(LOGS_DIR, f"{log_id}.meta")
    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail="Log not found")
    
    with open(metadata_path, 'r') as f:
        return json.load(f)


@app.get("/view_log/{log_id}")
async def view_log(log_id: str):
    """View log content (public, no auth required)"""
    log_path = os.path.join(LOGS_DIR, f"{log_id}.log")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Log not found")
    
    try:
        with open(log_path, 'rb') as f:
            content = f.read()
        
        # Try to decode as text
        try:
            text = content.decode('utf-8')
            # Try to parse as JSON
            try:
                return json.loads(text)
            except:
                return {"content": text}
        except:
            return {"content": content.hex(), "encoding": "hex"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log: {e}")


@app.get("/recent_logs")
async def get_recent_logs(minutes: int = 60):
    """Get recent logs metadata (public endpoint)"""
    cutoff_time = int(time.time()) - (minutes * 60)
    
    recent_logs = []
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith('.meta'):
            filepath = os.path.join(LOGS_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    metadata = json.load(f)
                    if metadata.get('timestamp', 0) > cutoff_time:
                        recent_logs.append(metadata)
            except:
                continue
    
    # Sort by timestamp (newest first)
    recent_logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    return {"logs": recent_logs, "count": len(recent_logs)}


@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    logs = [f for f in os.listdir(LOGS_DIR) if f.endswith('.log')]
    
    total_size = 0
    for log_file in logs:
        log_path = os.path.join(LOGS_DIR, log_file)
        total_size += os.path.getsize(log_path)
    
    return {
        "total_logs": len(logs),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "storage_limit_mb": round(MAX_STORAGE / 1024 / 1024, 2),
        "authorized_peers": len(AUTHORIZED_PEERS),
        "bandwidth_usage": {
            k[:8] + "...": v for k, v in list(bandwidth_usage.items())[:10]
        }
    }


@app.get("/contract_data")
async def get_contract_data():
    """Get all contract data files with fraudulent IPs"""
    contract_dir = os.getenv("CONTRACT_DIR", "/data/contract_data")
    
    if not os.path.exists(contract_dir):
        return {"files": []}
    
    files = []
    for filename in sorted(os.listdir(contract_dir), reverse=True):
        if filename.startswith('cd_'):
            filepath = os.path.join(contract_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    files.append({
                        "filename": filename,
                        "timestamp": data.get("t", 0),
                        "count": data.get("cnt", 0),
                        "entries": data.get("ent", [])
                    })
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return {"files": files[:100]}  # Return last 100 files


@app.get("/contract_data/{filename}")
async def get_contract_data_file(filename: str):
    """Get specific contract data file"""
    contract_dir = os.getenv("CONTRACT_DIR", "/data/contract_data")
    filepath = os.path.join(contract_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Contract data file not found")
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")


@app.post("/transfer_seka")
async def transfer_seka(request: TransferRequest):
    """Transfer SEKA tokens to recipient"""
    import subprocess
    
    recipient = request.recipient
    amount = request.amount
    
    try:
        print(f"[TRANSFER] Sending {amount} SEKA to {recipient}")
        
        # Call spl-token on host via docker exec (reverse approach)
        # Since we're in container, we need to call host's spl-token
        # Use bash to execute on host
        script_path = "/app/scripts/transfer_seka.sh"
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        result = subprocess.run(
            ["bash", script_path, recipient, str(amount)],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin:/root/.local/share/solana/install/active_release/bin"}
        )
        
        if result.returncode == 0:
            # Parse JSON response
            try:
                response = json.loads(result.stdout)
                if response.get("success"):
                    print(f"[TRANSFER] Success! Signature: {response.get('signature')}")
                    return {
                        "success": True,
                        "signature": response.get("signature"),
                        "amount": amount,
                        "recipient": recipient,
                        "message": f"Successfully sent {amount} SEKA"
                    }
                else:
                    error_msg = response.get("error", "Unknown error")
                    print(f"[TRANSFER] Failed: {error_msg}")
                    raise HTTPException(status_code=400, detail=error_msg)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid response from transfer script")
        else:
            error_msg = result.stderr or result.stdout
            print(f"[TRANSFER] Failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Transfer timeout")
    except Exception as e:
        print(f"[TRANSFER] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "9000")),
        log_level="info"
    )
