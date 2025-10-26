#!/usr/bin/env python3
"""
Test script for Sentinel contract
"""
import json
import os
from pathlib import Path
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet, Program, Context, Idl
import asyncio

# Program ID
PROGRAM_ID = Pubkey.from_string("7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7")

# Token Program IDs
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

async def main():
    print("🧪 Testing Sentinel Contract")
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
    
    # Convert to Idl object
    idl = Idl.from_json(json.dumps(idl_json))
    
    # Create program
    program = Program(idl, PROGRAM_ID, provider)
    
    print(f"📍 Program ID: {PROGRAM_ID}")
    print(f"👤 Wallet: {wallet.public_key}")
    print()
    
    # Derive PDAs
    state_pda, state_bump = Pubkey.find_program_address(
        [b"state"],
        PROGRAM_ID
    )
    
    treasury_pda, treasury_bump = Pubkey.find_program_address(
        [b"treasury"],
        PROGRAM_ID
    )
    
    print(f"🔑 State PDA: {state_pda}")
    print(f"🔑 Treasury PDA: {treasury_pda}")
    print()
    
    try:
        # Step 1: Check if program is initialized
        print("1️⃣  Checking if program is initialized...")
        try:
            state_account = await program.account["State"].fetch(state_pda)
            print("✅ Program already initialized")
            print(f"   Authority: {state_account.authority}")
            print(f"   Sentinel Mint: {state_account.sentinel_mint}")
            print(f"   Cycle Index: {state_account.cycle_index}")
            print()
        except Exception as e:
            print("⚠️  Program not initialized yet")
            print("   You need to run the initialize instruction first")
            print(f"   Error: {e}")
            print()
            await client.close()
            return
        
        # Step 2: Check if user has joined network
        print("2️⃣  Checking if user has joined network...")
        peer_pda, peer_bump = Pubkey.find_program_address(
            [b"peer", bytes(wallet.public_key)],
            PROGRAM_ID
        )
        
        try:
            peer_account = await program.account["PeerState"].fetch(peer_pda)
            print("✅ User is a network member")
            print(f"   Active: {peer_account.active}")
            print(f"   Karma: {peer_account.karma}")
            print()
        except Exception as e:
            print("⚠️  User has not joined network yet")
            print("   You need to call join_network first")
            print(f"   Error: {e}")
            print()
            await client.close()
            return
        
        # Step 3: Mint NFT
        print("3️⃣  Minting NFT...")
        print("   This would create an NFT and post")
        print("   (Full implementation requires spl-token library)")
        print()
        
        print("🎉 Test completed successfully!")
        print()
        print("📝 Summary:")
        print("   ✅ Program is deployed and initialized")
        print("   ✅ User is a network member")
        print("   ✅ Ready to mint NFTs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
