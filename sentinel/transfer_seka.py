#!/usr/bin/env python3
"""
Transfer SEKA tokens to a random address for testing
"""
import json
import asyncio
from pathlib import Path
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet
from spl.token.instructions import transfer_checked, TransferCheckedParams
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.transaction import Transaction

# Config
SOLANA_RPC = "http://localhost:8899"
SENTINEL_MINT = Pubkey.from_string("82UjXqRTyzNxkchsrwNmA7KgWgPFQ1QDDpUVo37ar6qE")
DECIMALS = 9
AMOUNT = 10_000 * (10 ** DECIMALS)  # 10,000 SEKA

def get_associated_token_address(mint: Pubkey, owner: Pubkey) -> Pubkey:
    """Calculate ATA"""
    TOKEN_PROGRAM_ID_PUBKEY = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    
    seeds = [bytes(owner), bytes(TOKEN_PROGRAM_ID_PUBKEY), bytes(mint)]
    return Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)[0]

async def main():
    print("💰 SEKA Token Transfer")
    print("=" * 50)
    print()
    
    # Load sender wallet
    wallet_path = Path.home() / ".config" / "solana" / "id.json"
    with open(wallet_path) as f:
        sender_keypair = Keypair.from_bytes(json.load(f))
    
    # Generate random recipient
    recipient_keypair = Keypair()
    
    print(f"From: {sender_keypair.pubkey()}")
    print(f"To:   {recipient_keypair.pubkey()}")
    print(f"Amount: {AMOUNT / (10 ** DECIMALS):,.0f} SEKA")
    print()
    
    # Setup connection
    client = AsyncClient(SOLANA_RPC, commitment=Confirmed)
    
    try:
        # Calculate ATAs
        sender_ata = get_associated_token_address(SENTINEL_MINT, sender_keypair.pubkey())
        recipient_ata = get_associated_token_address(SENTINEL_MINT, recipient_keypair.pubkey())
        
        print(f"Sender ATA: {sender_ata}")
        print(f"Recipient ATA: {recipient_ata}")
        print()
        
        # Check sender balance
        print("Checking sender balance...")
        sender_account = await client.get_token_account_balance(sender_ata)
        if sender_account.value:
            balance = int(sender_account.value.amount)
            print(f"Current balance: {balance / (10 ** DECIMALS):,.0f} SEKA")
            
            if balance < AMOUNT:
                print(f"❌ Insufficient balance! Need {AMOUNT / (10 ** DECIMALS):,.0f} SEKA")
                return
        else:
            print("❌ Sender ATA not found!")
            return
        
        print()
        print("Creating recipient ATA and transferring tokens...")
        
        # Create ATA instruction
        from spl.token.instructions import create_associated_token_account
        from solders.system_program import ID as SYS_PROGRAM_ID
        
        ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
        
        create_ata_ix = create_associated_token_account(
            payer=sender_keypair.pubkey(),
            owner=recipient_keypair.pubkey(),
            mint=SENTINEL_MINT,
        )
        
        # Create transfer instruction
        transfer_ix = transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=sender_ata,
                mint=SENTINEL_MINT,
                dest=recipient_ata,
                owner=sender_keypair.pubkey(),
                amount=AMOUNT,
                decimals=DECIMALS,
            )
        )
        
        # Get recent blockhash
        blockhash_resp = await client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash
        
        # Create transaction with both instructions
        from solders.message import Message
        
        msg = Message.new_with_blockhash(
            [create_ata_ix, transfer_ix],
            sender_keypair.pubkey(),
            recent_blockhash
        )
        
        tx = Transaction([sender_keypair], msg, recent_blockhash)
        
        # Send transaction
        result = await client.send_transaction(tx)
        signature = result.value
        
        print(f"✅ Transfer successful!")
        print(f"   Signature: {signature}")
        print()
        
        # Verify recipient balance
        print("Verifying recipient balance...")
        await asyncio.sleep(2)  # Wait for confirmation
        
        recipient_account = await client.get_token_account_balance(recipient_ata)
        if recipient_account.value:
            new_balance = int(recipient_account.value.amount)
            print(f"✅ Recipient balance: {new_balance / (10 ** DECIMALS):,.0f} SEKA")
        
        print()
        print("📝 Recipient Info:")
        print(f"   Keypair saved to: recipient_keypair.json")
        print(f"   Public Key: {recipient_keypair.pubkey()}")
        print(f"   ATA: {recipient_ata}")
        
        # Save recipient keypair
        with open("recipient_keypair.json", "w") as f:
            json.dump(list(bytes(recipient_keypair)), f)
        
        print()
        print("✅ Done! You can now test with this recipient.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
