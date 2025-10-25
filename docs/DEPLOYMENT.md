# 🚀 Deployment Guide

## Quick Deploy to Local Testnet

```bash
# 1. Start Solana testnet
cd solanaTestNetDocker
./manager.sh --validate

# 2. Deploy contract
cd ..
./deploy-sentinel-local.sh 2

# Done! Contract deployed to localhost:8899
```

## Deployment Options

### Local Development

```bash
# Using default key [2]
./deploy-sentinel-local.sh 2

# Using different key
./deploy-sentinel-local.sh 3
```

### Devnet Deployment

```bash
cd sentinel
anchor deploy --provider.cluster devnet
```

### Mainnet Deployment

```bash
cd sentinel
anchor deploy --provider.cluster mainnet-beta
```

## What Gets Deployed

1. **Sentinel Smart Contract** - Karma rewards and NFT minting
2. **Program ID** - `Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V`
3. **Authority** - Deployment key has upgrade authority

## Post-Deployment

### Initialize Contract

```bash
cd sentinel
anchor test --skip-local-validator
```

### Verify Deployment

```bash
solana account Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V --url http://localhost:8899
```

## Files Created

- `sentinel/deploy-keypair.json` - Deployment keypair
- `sentinel/target/deploy/sentinel.so` - Compiled program
- `sentinel/target/deploy/sentinel-keypair.json` - Program keypair

## Troubleshooting

### Testnet Not Running

```bash
cd solanaTestNetDocker
./manager.sh --validate
```

### Need More SOL

```bash
cd solanaTestNetDocker
./keymanager.sh --airdrop -n 2 1000
```

### Check Balance

```bash
cd solanaTestNetDocker
./keymanager.sh --balance -n 2
```

## Security Notes

⚠️ **Important**: 
- Keep `deploy-keypair.json` secure (has upgrade authority)
- For production, use hardware wallet or multisig
- Consider making program immutable after testing

## See Also

- [DEPLOY_LOCAL.md](../DEPLOY_LOCAL.md) - Detailed local deployment
- [Sentinel README](../sentinel/README.md) - Contract documentation