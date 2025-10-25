# Mint and Upload Contract Logs

This script uploads all contract data logs to the HTTP log server and mints NFTs for them on the Sentinel contract.

## Prerequisites

1. **Log server running** (`./manager.sh --monitor`)
2. **Solana testnet running** (`cd solanaTestNetDocker && ./manager.sh --validate`)
3. **Python 3** with `requests` library
4. **Solana CLI tools** (`solana`, `spl-token`, `solana-keygen`)
5. **Deployment keypair** (`./sentinel/deploy-keypair.json`)

## Quick Start

```bash
# Install dependencies
pip install requests

# Run the script
python3 scripts/mint_and_upload_logs.py
```

## What It Does

For each `.log` file in `data/contract_data/`:

1. **Computes SHA256 hash** of the file
2. **Uploads to log server** at `http://localhost:9000`
3. **Creates NFT mint** (0 decimals) on Solana
4. **Mints NFT** on Sentinel contract with:
   - Log URL (e.g., `http://localhost:9000/logs/abc123`)
   - File hash (SHA256)
   - Metadata stored on-chain

## Configuration

Environment variables:

```bash
export RPC_URL="http://localhost:8899"              # Solana RPC
export KEYPAIR_PATH="./sentinel/deploy-keypair.json"  # Deployer key
export CONTRACT_DATA_DIR="./data/contract_data"     # Log files directory
export LOG_SERVER_URL="http://localhost:9000"       # Log server
```

## Testing Mode

The log server is in **TESTING MODE** by default:
- ✓ No signature verification required
- ✓ All uploads allowed
- ✓ All downloads allowed
- ✓ No peer authorization needed

This is for development only. For production, set `TESTING_MODE=false`.

## Example Output

```
╔════════════════════════════════════════════════════════════╗
║     Mint NFTs and Upload Contract Data Logs               ║
╚════════════════════════════════════════════════════════════╝

[INFO] Loading keypair from: ./sentinel/deploy-keypair.json
[INFO] Payer: FKYCbhJfA4K5rVqFdunr55LXT6Qo5kbG5uxEPGkW1iCc

[INFO] Checking log server: http://localhost:9000
[INFO] Log server status: healthy
  Logs stored: 0
  Storage used: 0.0 MB

[INFO] Checking Solana RPC: http://localhost:8899

[INFO] Scanning directory: ./data/contract_data
[INFO] Found 5 log files:
  [1] cd_1760566500_15_10_25_22_15_00.log
  [2] cd_1760566680_15_10_25_22_18_00.log
  [3] cd_1760566860_15_10_25_22_21_00.log
  [4] cd_1760567040_15_10_25_22_24_00.log
  [5] cd_1760567220_15_10_25_22_27_00.log

[WARN] This will:
  1. Upload 5 files to http://localhost:9000
  2. Create 5 NFT mints
  3. Mint 5 NFTs on Sentinel contract

[WARN] TESTING MODE: All downloads allowed (no signature verification)

Continue? (yes/no): yes

============================================================
Starting processing...
============================================================

============================================================
Processing: cd_1760566500_15_10_25_22_15_00.log
============================================================
[1/4] Computing file hash...
  Hash: a1b2c3d4e5f6...
  Size: 12345 bytes
[2/4] Uploading to log server...
  ✓ Uploaded successfully!
    Log ID: a1b2c3d4e5f6
    URL: http://localhost:9000/logs/a1b2c3d4e5f6
  ✓ Hash verified!
[3/4] Creating NFT mint...
  ✓ NFT mint created: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
[4/4] Minting NFT on Sentinel contract...
  [INFO] Would call Sentinel.mint_nft():
    mint: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
    url: http://localhost:9000/logs/a1b2c3d4e5f6
    hash: a1b2c3d4e5f6...
  [WARN] Skipping on-chain mint (not implemented yet)

✓ Successfully processed cd_1760566500_15_10_25_22_15_00.log
  NFT Mint: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
  Log URL: http://localhost:9000/logs/a1b2c3d4e5f6

...

============================================================
Processing Summary
============================================================
Total files:    5
Success:        5
Failed:         0
============================================================

Detailed Results:
  ✓ cd_1760566500_15_10_25_22_15_00.log: SUCCESS
  ✓ cd_1760566680_15_10_25_22_18_00.log: SUCCESS
  ✓ cd_1760566860_15_10_25_22_21_00.log: SUCCESS
  ✓ cd_1760567040_15_10_25_22_24_00.log: SUCCESS
  ✓ cd_1760567220_15_10_25_22_27_00.log: SUCCESS

============================================================
Next Steps:
============================================================
1. View uploaded logs: curl http://localhost:9000/stats
2. Download a log: curl http://localhost:9000/logs/<log_id>
3. Check log server: curl http://localhost:9000/health
============================================================
```

## Verify Uploads

Check log server stats:
```bash
curl http://localhost:9000/stats
```

View health:
```bash
curl http://localhost:9000/health
```

List uploaded logs:
```bash
ls -lh data/logs/
```

Download a log:
```bash
curl http://localhost:9000/logs/<log_id> \
  -H "X-Peer-Pubkey: FKYCbhJfA4K5rVqFdunr55LXT6Qo5kbG5uxEPGkW1iCc" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Signature: test" \
  -o downloaded.log
```

## Troubleshooting

**Log server not running:**
```bash
./manager.sh --monitor
```

**Solana testnet not running:**
```bash
cd solanaTestNetDocker
./manager.sh --validate
```

**Missing dependencies:**
```bash
pip install requests
```

**Solana CLI not found:**
```bash
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
```

## Notes

- The script currently **skips the on-chain NFT minting** (placeholder)
- To implement actual minting, you need to integrate with Anchor
- Files are uploaded and stored on the log server
- NFT mints are created but not yet linked to the Sentinel contract
- This is a testing/development version

## Next Steps

To complete the implementation:

1. Install Anchor Python SDK: `pip install anchorpy`
2. Generate IDL for Sentinel contract
3. Implement the `mint_nft_on_chain()` function
4. Call Sentinel contract's `mint_nft` instruction
5. Pass the log URL and file hash to the contract
