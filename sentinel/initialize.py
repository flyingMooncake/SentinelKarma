#!/usr/bin/env python3
"""
Initialize the Sentinel contract
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
    print("🚀 Initializing Sentinel Contract")
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
    print(f"👤 Authority: {wallet.public_key}")
    print()
    
    try:
        # Derive PDAs
        state_pda, _ = Pubkey.find_program_address([b"state"], PROGRAM_ID)
        treasury_pda, _ = Pubkey.find_program_address([b"treasury"], PROGRAM_ID)
        
        # Create new mint keypair for Sentinel token
        sentinel_mint = Keypair()
        
        # Calculate ATAs
        authority_ata = get_associated_token_address(sentinel_mint.pubkey(), wallet.public_key)
        treasury_ata = get_associated_token_address(sentinel_mint.pubkey(), treasury_pda)
        
        print("🔑 Accounts:")
        print(f"   State PDA: {state_pda}")
        print(f"   Treasury PDA: {treasury_pda}")
        print(f"   Sentinel Mint: {sentinel_mint.pubkey()}")
        print(f"   Authority ATA: {authority_ata}")
        print(f"   Treasury ATA: {treasury_ata}")
        print()
        
        print("📤 Sending initialize transaction...")
        
        # Call initialize
        tx = await program.rpc["initialize"](
            ctx=Context(
                accounts={
                    "authority": wallet.public_key,
                    "state": state_pda,
                    "sentinel_mint": sentinel_mint.pubkey(),
                    "treasury_vault": treasury_pda,
                    "authority_sentinel_ata": authority_ata,
                    "treasury_sentinel_ata": treasury_ata,
                    "token_program": TOKEN_PROGRAM_ID,
                    "associated_token_program": ASSOCIATED_TOKEN_PROGRAM_ID,
                    "system_program": SYS_PROGRAM_ID,
                    "rent": RENT,
                },
                signers=[sentinel_mint],
            )
        )
        
        print(f"✅ Initialize successful!")
        print(f"   Transaction: {tx}")
        print()
        
        # Verify state was created
        print("🔍 Verifying initialization...")
        state_account = await program.account["State"].fetch(state_pda)
        print(f"✅ State account created")
        print(f"   Authority: {state_account.authority}")
        print(f"   Sentinel Mint: {state_account.sentinel_mint}")
        print(f"   Treasury Vault: {state_account.treasury_vault}")
        print(f"   Cycle Index: {state_account.cycle_index}")
        print()
        
        print("🎉 Initialization complete!")
        print()
        print("📝 Next steps:")
        print("   1. Run: python3 test_mint.py")
        print("   2. You should see that you need to join the network")
        print("   3. Then you can mint NFTs!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
