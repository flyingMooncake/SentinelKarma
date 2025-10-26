#!/usr/bin/env python3
"""
Complete NFT minting with SPL token creation
"""
import json
from pathlib import Path
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from solders.instruction import Instruction, AccountMeta
from solders.transaction import Transaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from anchorpy import Provider, Wallet, Program, Idl, Context
import asyncio
import struct

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

def create_mint_instruction(mint_pubkey: Pubkey, authority: Pubkey, decimals: int = 0) -> Instruction:
    """Create instruction to initialize a mint"""
    # InitializeMint instruction (discriminator 0)
    data = bytes([0]) + struct.pack("<B", decimals) + bytes(authority) + bytes([0]) + bytes(32)
    
    return Instruction(
        program_id=TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(pubkey=mint_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        ],
        data=data
    )

async def main():
    print("🎨 Minting NFT on Sentinel")
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
        peer_pda, _ = Pubkey.find_program_address([b"peer", bytes(wallet.public_key)], PROGRAM_ID)
        
        # Create NFT mint keypair
        nft_mint = Keypair()
        print(f"🎨 Creating NFT...")
        print(f"   NFT Mint: {nft_mint.pubkey()}")
        
        # Calculate addresses
        user_nft_ata = get_associated_token_address(nft_mint.pubkey(), wallet.public_key)
        post_pda, _ = Pubkey.find_program_address([b"post", bytes(nft_mint.pubkey())], PROGRAM_ID)
        
        # Create hash and db_addr
        hash_data = [42] * 32  # Example hash
        db_addr = Keypair().pubkey()  # Random database address
        
        print(f"   User NFT ATA: {user_nft_ata}")
        print(f"   Post PDA: {post_pda}")
        print(f"   DB Address: {db_addr}")
        print()
        
        print("📤 Sending mint_nft transaction...")
        
        # Call mint_nft (Anchor will create the mint and ATA automatically)
        tx = await program.rpc["mint_nft"](
            hash_data,
            db_addr,
            ctx=Context(
                accounts={
                    "user": wallet.public_key,
                    "state": state_pda,
                    "peer": peer_pda,
                    "nft_mint": nft_mint.pubkey(),
                    "user_nft_ata": user_nft_ata,
                    "post": post_pda,
                    "token_program": TOKEN_PROGRAM_ID,
                    "associated_token_program": ASSOCIATED_TOKEN_PROGRAM_ID,
                    "system_program": SYS_PROGRAM_ID,
                    "rent": RENT,
                },
                signers=[nft_mint],
            )
        )
        
        print(f"✅ NFT minted successfully!")
        print(f"   Transaction: {tx}")
        print()
        
        # Fetch and display post
        print("🔍 Fetching post data...")
        post_account = await program.account["Post"].fetch(post_pda)
        print(f"✅ Post created!")
        print(f"   Owner: {post_account.owner}")
        print(f"   NFT Mint: {post_account.nft_mint}")
        print(f"   Hash: {bytes(post_account.hash).hex()[:16]}...")
        print(f"   DB Address: {post_account.db_addr}")
        print(f"   Likes: {post_account.likes}")
        print(f"   Cycle Index: {post_account.cycle_index}")
        print()
        
        print("🎉 NFT Minting Complete!")
        print()
        print("📝 Summary:")
        print(f"   ✅ NFT Mint: {nft_mint.pubkey()}")
        print(f"   ✅ Post PDA: {post_pda}")
        print(f"   ✅ Transaction: {tx}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
