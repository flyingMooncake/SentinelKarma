#!/bin/bash
# Simple NFT minting using Solana CLI + Python

set -e

echo "🎨 Minting NFT on Sentinel"
echo "================================"
echo ""

# Create NFT mint (0 decimals)
echo "1️⃣  Creating NFT mint..."

# Create temporary keypair for the mint
TEMP_KEYPAIR=$(mktemp -u).json
solana-keygen new --no-bip39-passphrase --outfile $TEMP_KEYPAIR --force
NFT_MINT=$(solana-keygen pubkey $TEMP_KEYPAIR)
echo "   NFT Mint: $NFT_MINT"

# Create the mint account with 0 decimals
spl-token create-token --decimals 0 $TEMP_KEYPAIR
rm -f $TEMP_KEYPAIR

echo ""
echo "2️⃣  Calling mint_nft instruction..."

# Now call Python to invoke the contract
python3 - <<EOF
import json
import asyncio
from pathlib import Path
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet, Program, Idl, Context
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT

PROGRAM_ID = Pubkey.from_string("7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7")
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

def get_ata(mint, owner):
    seeds = [bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)]
    return Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)[0]

async def main():
    client = AsyncClient("http://localhost:8899", commitment=Confirmed)
    wallet_path = Path.home() / ".config" / "solana" / "id.json"
    with open(wallet_path) as f:
        keypair = Keypair.from_bytes(json.load(f))
    wallet = Wallet(keypair)
    provider = Provider(client, wallet)
    
    idl_path = Path("target/idl/sentinel.json")
    with open(idl_path) as f:
        idl = Idl.from_json(json.dumps(json.load(f)))
    
    program = Program(idl, PROGRAM_ID, provider)
    
    nft_mint = Pubkey.from_string("$NFT_MINT")
    state_pda, _ = Pubkey.find_program_address([b"state"], PROGRAM_ID)
    peer_pda, _ = Pubkey.find_program_address([b"peer", bytes(wallet.public_key)], PROGRAM_ID)
    user_nft_ata = get_ata(nft_mint, wallet.public_key)
    post_pda, _ = Pubkey.find_program_address([b"post", bytes(nft_mint)], PROGRAM_ID)
    
    hash_data = [42] * 32
    db_addr = Keypair().pubkey()
    
    print(f"   Post PDA: {post_pda}")
    print(f"   DB Address: {db_addr}")
    print("")
    
    tx = await program.rpc["mint_nft"](
        hash_data, db_addr,
        ctx=Context(accounts={
            "user": wallet.public_key,
            "state": state_pda,
            "peer": peer_pda,
            "nft_mint": nft_mint,
            "user_nft_ata": user_nft_ata,
            "post": post_pda,
            "token_program": TOKEN_PROGRAM_ID,
            "associated_token_program": ASSOCIATED_TOKEN_PROGRAM_ID,
            "system_program": SYS_PROGRAM_ID,
            "rent": RENT,
        })
    )
    
    print(f"✅ NFT minted!")
    print(f"   Transaction: {tx}")
    print("")
    
    post = await program.account["Post"].fetch(post_pda)
    print(f"📄 Post Details:")
    print(f"   Owner: {post.owner}")
    print(f"   NFT Mint: {post.nft_mint}")
    print(f"   Likes: {post.likes}")
    print("")
    print("🎉 Success!")
    
    await client.close()

asyncio.run(main())
EOF

echo ""
echo "✅ NFT Minting Complete!"
