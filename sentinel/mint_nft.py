#!/usr/bin/env python3
"""
Complete flow: Check peer status, join if needed, then mint NFT
"""
import json
from pathlib import Path
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet, Program, Idl, Context
import asyncio

# Program ID
PROGRAM_ID = Pubkey.from_string("7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7")

# Token Program IDs
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

def get_associated_token_address(mint: Pubkey, owner: Pubkey) -> Pubkey:
    """Calculate associated token address"""
    seeds = [
        bytes(owner),
        bytes(TOKEN_PROGRAM_ID),
        bytes(mint),
    ]
    return Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)[0]

async def main():
    print("🚀 Sentinel NFT Minting Flow")
    print("=" * 50)
    print()

    # Setup connection
    client = AsyncClient("http://localhost:8899", commitment=Confirmed)
    
    # Load wallet
    wallet_path = Path.home() / ".config" / "solana" / "id.json"
    with open(wallet_path) as f:
        secret_key = json.load(f)
    
    keypair = Keypair.from_bytes(secret_key)
    wallet = Wallet(keypair)
    
    # Create provider
    provider = Provider(client, wallet)
    
    # Load IDL
    idl_path = Path(__file__).parent / "target" / "idl" / "sentinel.json"
    with open(idl_path) as f:
        idl_json = json.load(f)
    
    idl = Idl.from_json(json.dumps(idl_json))
    program = Program(idl, PROGRAM_ID, provider)
    
    print(f"📍 Program ID: {PROGRAM_ID}")
    print(f"👤 Wallet: {wallet.public_key}")
    print()
    
    try:
        # Derive PDAs
        state_pda, _ = Pubkey.find_program_address([b"state"], PROGRAM_ID)
        treasury_pda, _ = Pubkey.find_program_address([b"treasury"], PROGRAM_ID)
        peer_pda, _ = Pubkey.find_program_address([b"peer", bytes(wallet.public_key)], PROGRAM_ID)
        
        # Get state
        state_account = await program.account["State"].fetch(state_pda)
        sentinel_mint = state_account.sentinel_mint
        
        print(f"🔑 Sentinel Mint: {sentinel_mint}")
        print()
        
        # Step 1: Check if peer is in network
        print("1️⃣  Checking peer status...")
        is_peer = False
        try:
            peer_account = await program.account["PeerState"].fetch(peer_pda)
            print(f"✅ Already a network member!")
            print(f"   Active: {peer_account.active}")
            print(f"   Karma: {peer_account.karma}")
            is_peer = True
        except:
            print("⚠️  Not a network member yet")
        print()
        
        # Step 2: Join network if needed
        if not is_peer:
            print("2️⃣  Joining network...")
            
            # Calculate ATAs
            user_ata = get_associated_token_address(sentinel_mint, wallet.public_key)
            treasury_ata = get_associated_token_address(sentinel_mint, treasury_pda)
            
            print(f"   User ATA: {user_ata}")
            print(f"   Treasury ATA: {treasury_ata}")
            print(f"   Cost: 1000 SEKA")
            print()
            
            # Join network
            tx = await program.rpc["join_network"](
                ctx=Context(
                    accounts={
                        "user": wallet.public_key,
                        "state": state_pda,
                        "peer": peer_pda,
                        "user_sentinel_ata": user_ata,
                        "treasury_vault": treasury_pda,
                        "treasury_sentinel_ata": treasury_ata,
                        "token_program": TOKEN_PROGRAM_ID,
                        "system_program": SYS_PROGRAM_ID,
                    }
                )
            )
            
            print(f"✅ Joined network!")
            print(f"   Transaction: {tx}")
            print()
        
        # Step 3: Mint NFT
        print("3️⃣  Minting NFT...")
        
        # Create NFT mint keypair
        nft_mint = Keypair()
        print(f"   NFT Mint: {nft_mint.pubkey()}")
        
        # Calculate addresses
        user_nft_ata = get_associated_token_address(nft_mint.pubkey(), wallet.public_key)
        post_pda, _ = Pubkey.find_program_address([b"post", bytes(nft_mint.pubkey())], PROGRAM_ID)
        
        # Create hash and db_addr
        hash_data = [1] * 32  # Simple hash
        db_addr = Keypair().pubkey()  # Random database address
        
        print(f"   Post PDA: {post_pda}")
        print(f"   DB Address: {db_addr}")
        print()
        
        # Note: This will fail because we need to create the NFT mint first
        # The full implementation requires using spl-token to create the mint
        print("⚠️  Note: Full NFT minting requires creating the mint first")
        print("   This would need spl-token library integration")
        print()
        
        print("🎉 Flow completed!")
        print()
        print("📝 Summary:")
        print(f"   ✅ Peer status checked")
        if not is_peer:
            print(f"   ✅ Joined network (paid 1000 SEKA)")
        print(f"   ⚠️  NFT minting ready (needs mint creation)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
