# Sentinel Program

Solana program using Anchor. Features:
- SentinelCoin mint (9 decimals)
- Pay 1000 SentinelCoin to join as peer
- Peers can mint NFTs (0-decimal SPL mint) and publish posts referencing a hash and a DB address
- Likes from peers award karma to the NFT owner
- Every 2 hours, distribute 1000 Sentinel proportionally to karma with a 10% per-peer cap
- Mint 100k Sentinel to deployer on initialize

## Program IDs
Change the program ID everywhere before deploy/build:
1. Generate key: `anchor keys list` (or `anchor keys create sentinel`)
2. Sync keys: `anchor keys sync`
3. Update declare_id! in `programs/sentinel/src/lib.rs` if needed.

## Build
```
anchor build --no-idl
```
Note: IDL generation is disabled due to version compatibility. The program binary builds successfully.

## Localnet
In one terminal:
```
solana-test-validator
```

In another terminal:
```
anchor deploy
```

## Tests
Install deps and run:
```
npm install
anchor test
```

The tests cover:
- initialize: creates mint, mints 100k to authority
- join_network: authority and a second peer join; 1000 token fee paid to treasury
- mint_nft: active peer mints a 0-decimal NFT and creates a Post
- like_nft: another active peer likes the post; owner’s karma increments
- finalize_cycle: verifies it fails before 2 hours have elapsed

## Instruction Overview
- initialize(authority)
  - Creates State PDA, Treasury Vault PDA, SentinelCoin mint (authority = State), and mints 100,000 to authority ATA.
- join_network(user)
  - Transfers 1000 Sentinel from user ATA to treasury ATA; creates/activates PeerState.
- mint_nft(user, nft_mint, user_nft_ata, post)
  - Requires peer active; NFT mint must be 0 decimals and mint_authority=user; mints 1 token to user ATA; records Post { hash, db_addr }.
- like_nft(liker, post)
  - Requires liker is active peer; creates Like PDA; increments Post.likes and owner PeerState.karma.
- finalize_cycle(authority, peers[], karmas[], remaining: ATAs)
  - After 2 hours, distribute 1000 Sentinel across peers proportionally to provided karma; cap 100 per peer. Validates remaining accounts as peer ATAs for Sentinel mint.

## Notes
- The cycle reward is minted each cycle; treasury accumulates join fees (future use TBD).
- For shorter test cycles, add a feature flag path to bypass the 2h window.
- For full NFT metadata, integrate Metaplex later.
