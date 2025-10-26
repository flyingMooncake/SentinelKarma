# ⚙️ Auto Mint Configuration Guide

## 📁 Configuration File

**Location**: `/home/water/SentinelKarma/scripts/auto_mint.conf`

---

## 🎯 Your Settings

### Mint Timing
- **CHECK_INTERVAL=30** - Checks for new logs every 30 seconds
- **MINT_DELAY=2** - 2 second delay between processing files

### Burst Protection
- **OVERBURST_DURATION=180** - Tracks mints over 3 minutes (180 seconds)
- **BURST_COOLDOWN=10** - 10 second cooldown after burst detected
- **BURST_DURATION=5** - Burst window of 5 seconds
- **BURST_THRESHOLD=5** - Triggers if 5+ files minted in 5 seconds

---

## 🔥 How Burst Protection Works

```
Timeline Example:
─────────────────────────────────────────────────────────
T=0s    T=1s    T=2s    T=3s    T=4s    T=5s    T=15s
 │       │       │       │       │       │       │
Mint1  Mint2  Mint3  Mint4  Mint5  BURST!  Resume
                                    ↓
                              Cooldown 10s
```

### Scenario 1: Normal Operation
```
- File 1 detected → Mint → Success
- Wait 2s (MINT_DELAY)
- File 2 detected → Mint → Success
- Wait 2s
- Continue...
```

### Scenario 2: Burst Detected
```
- 5 files minted within 5 seconds
- ⚠️  BURST DETECTED!
- 🛑 Enter cooldown for 10 seconds
- ⏸️  Skip all processing during cooldown
- ✅ Resume after cooldown
```

### Scenario 3: Overburst Tracking
```
- Tracks all mints in last 180 seconds
- Shows stats: "Mints in last 180s: 15"
- Helps monitor overall activity
- Old timestamps automatically cleaned
```

---

## 📊 Configuration Explained

### CHECK_INTERVAL (30 seconds)
```python
# Every 30 seconds, the monitor:
1. Scans data/malicious_logs/ directory
2. Finds new .log files
3. Checks if already processed
4. Processes new files
```

### BURST_DURATION (5 seconds)
```python
# If 5+ files are minted within 5 seconds:
- Burst protection triggers
- Enters cooldown mode
- Prevents overwhelming the blockchain
```

### BURST_COOLDOWN (10 seconds)
```python
# During cooldown:
- No files are processed
- Monitor shows countdown
- After 10s, resumes normal operation
```

### OVERBURST_DURATION (180 seconds)
```python
# Tracks mints over 3 minutes:
- Keeps history of recent mints
- Shows statistics
- Cleans old timestamps
```

---

## 🎛️ Customizing Settings

### Edit Configuration

```bash
nano /home/water/SentinelKarma/scripts/auto_mint.conf
```

### Example Modifications

#### Faster Checking (15 seconds)
```bash
CHECK_INTERVAL=15
```

#### More Aggressive Burst Protection
```bash
BURST_THRESHOLD=3      # Trigger after 3 files
BURST_DURATION=10      # Within 10 seconds
BURST_COOLDOWN=30      # Cooldown for 30 seconds
```

#### Relaxed Burst Protection
```bash
BURST_THRESHOLD=10     # Allow 10 files
BURST_DURATION=3       # Within 3 seconds
BURST_COOLDOWN=5       # Short cooldown
```

#### Disable Burst Protection
```bash
BURST_THRESHOLD=999999  # Effectively disabled
```

---

## 📈 Monitoring

### Watch Live Activity

```bash
cd /home/water/SentinelKarma
python3 scripts/auto_mint_complete.py
```

### Output Example

```
[2025-01-26 12:30:00] Scanning...
[INFO] Found 3 new file(s)

[1234567890_26_01_25_12_30_00.log]
  Hash: abc123def456...
  Uploading to log server...
  ✓ Uploaded! URL: http://...
  Minting NFT on Sentinel...
    Creating NFT mint...
    NFT Mint: 5x7y9z...
    Calling mint_nft instruction...
    ✓ NFT minted! TX: 2uq9AU...
  ✓ NFT minted!
[SUCCESS] Processed 1234567890_26_01_25_12_30_00.log
[STATS] Mints in last 5s: 1
[STATS] Mints in last 180s: 1

[2025-01-26 12:30:05] Scanning...
[INFO] Found 5 new file(s)
[BURST] ⚠️  Burst detected! 5 mints in 5s
[BURST] Entering cooldown for 10s...

[2025-01-26 12:30:06] 🛑 COOLDOWN - 9s remaining...
[2025-01-26 12:30:11] 🛑 COOLDOWN - 4s remaining...
[2025-01-26 12:30:15] ✅ Cooldown ended, resuming...
```

---

## 🔧 Environment Variables

You can override config file settings with environment variables:

```bash
# Override check interval
export CHECK_INTERVAL=15

# Override burst settings
export BURST_THRESHOLD=10
export BURST_COOLDOWN=20

# Run with overrides
python3 scripts/auto_mint_complete.py
```

---

## 📝 Configuration Priority

1. **Environment Variables** (highest priority)
2. **Config File** (`auto_mint.conf`)
3. **Default Values** (lowest priority)

Example:
```bash
# Config file says: CHECK_INTERVAL=30
# Environment says: CHECK_INTERVAL=15
# Result: Uses 15 (environment wins)
```

---

## 🎯 Recommended Settings

### Development/Testing
```bash
CHECK_INTERVAL=10      # Fast checking
BURST_THRESHOLD=10     # Relaxed
BURST_COOLDOWN=5       # Short cooldown
```

### Production
```bash
CHECK_INTERVAL=30      # Your current setting ✅
BURST_THRESHOLD=5      # Your current setting ✅
BURST_COOLDOWN=10      # Your current setting ✅
OVERBURST_DURATION=180 # Your current setting ✅
```

### High Volume
```bash
CHECK_INTERVAL=60      # Less frequent
BURST_THRESHOLD=20     # Allow more
BURST_COOLDOWN=30      # Longer cooldown
```

---

## 📊 Statistics Tracking

The monitor tracks:
- **Total files processed**
- **Mints in last 5 seconds** (burst window)
- **Mints in last 180 seconds** (overburst window)
- **Cooldown status**
- **Success/failure rates**

All saved to `nft_mappings.json`

---

## 🚀 Quick Start

```bash
# 1. Edit config if needed
nano scripts/auto_mint.conf

# 2. Run monitor
python3 scripts/auto_mint_complete.py

# 3. Watch it work!
```

---

## ✅ Your Current Configuration Summary

| Setting | Value | Purpose |
|---------|-------|---------|
| CHECK_INTERVAL | 30s | Check for new logs every 30 seconds |
| OVERBURST_DURATION | 180s | Track mints over 3 minutes |
| BURST_COOLDOWN | 10s | Wait 10 seconds after burst |
| BURST_DURATION | 5s | Burst window |
| BURST_THRESHOLD | 5 files | Trigger after 5 files in 5s |
| MINT_DELAY | 2s | Delay between processing files |

**Perfect for production use!** ✅
