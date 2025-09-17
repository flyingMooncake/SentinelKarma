# Solana On-chain Contracts — Karma System

Status: Design Spec (MVP on-chain)
Target Framework: Anchor (Rust)

Summary
- Introduces non-transferable Karma Points (KP) and a fungible SPL token SentinelKarmaToken (SEKA).
- KP are earned per cycle (3 days) from off-chain scoring: likes on reports and corroborated detections.
- Each cycle distributes up to 10,000 KP total across peers; per-peer net delta capped at 100 KP.
- KP can be converted into SEKA at 100 KP = 1 SEKA.
- Joining the network requires paying 10 SEKA (configurable by governance).
- Spam/low-quality behavior results in negative KP deltas (clamped to prevent underflow below 0 in ledger).
- On program initialization, 10,000 SEKA are airdropped to a chosen public key.

Design Principles
- Minimal on-chain footprint: use per-cycle Merkle roots for KP distributions (and penalties) signed by a Governor.
- Deterministic PDAs for program state, ledgers, and cycle roots.
- SPL Token for SEKA mint with program PDA as mint authority.
- Configurable parameters via Governor (multisig or external governance CPI).

Glossary
- KP: Karma Points (non-transferable, on-chain ledger per peer)
- SEKA: SPL token minted by conversion from KP
- Cycle: 3-day scoring window (configurable)
- Governor: authority allowed to set roots and update config (can be multisig or SPL Governance)

Tokenomics (initial parameters)
- cycle_secs: 259200 (3 days)
- max_points_per_cycle: 10,000 KP
- per_peer_cycle_cap: 100 KP (net delta in a cycle)
- conversion_ratio: 100 KP -> 1 SEKA
- join_cost_tokens: 10 SEKA (configurable)
- airdrop_on_init: 10,000 SEKA to a provided pubkey
- SEKA decimals: 6

Accounts and PDAs
1) GlobalConfig (PDA: ["config"])
   - bump: u8
   - governor: Pubkey          // authority to update config and set cycle roots
   - treasury: Pubkey          // SEKA token account (PDA) receiving join payments
   - mint: Pubkey              // SEKA SPL mint address
   - mint_authority: Pubkey    // PDA owning mint authority
   - cycle_secs: u64           // default 259200
   - max_points_per_cycle: u32 // default 10_000
   - per_peer_cycle_cap: i32   // default 100 (applies to |delta| and net)
   - conversion_ratio: u32     // KP per 1 SEKA, default 100
   - join_cost_tokens: u64     // in base units (decimals=6), default 10 * 10^6
   - start_ts: i64             // epoch when cycle 0 starts
   - airdrop_done: bool

2) CycleState (PDA: ["cycle", cycle_index:u64])
   - bump: u8
   - cycle_index: u64
   - merkle_root: [u8; 32]     // keccak or blake3 root of (peer, cycle, delta)
   - total_points_declared: u32// declared sum for audit; must be <= max_points_per_cycle
   - claims_bitmap: Vec<u8>    // packed bits for claim slots (see leaf indexing scheme)

3) PeerLedger (PDA: ["peer", peer_pubkey])
   - bump: u8
   - owner: Pubkey             // peer pubkey
   - points: i64               // current KP balance (>= 0 enforced)
   - last_cycle_claimed: u64   // highest cycle in which a claim was processed (for info)

4) Membership (PDA: ["member", member_pubkey])
   - bump: u8
   - owner: Pubkey
   - joined_at: i64            // unix ts
   - active: bool

5) Treasury Token Account (PDA: ["treasury"], SEKA mint)
   - Program-derived associated token account holding join payments.

6) Mint Authority PDA (PDA: ["mint_authority"]) — set as mint authority of SEKA SPL mint.

7) Optional: Guardian/Multisig (external)
   - We recommend using an external multisig or SPL Governance to control governor. For MVP, a single governor key is acceptable.

Merkle Distribution (per cycle)
- Leaf format (serialized, hashed):
  struct Leaf { owner: Pubkey, cycle_index: u64, delta_points: i32, index: u32 }
- Off-chain aggregator builds a tree of leaves for all peers with non-zero delta.
- Constraints enforced off-chain and by Governor before setting root:
  - sum(|positive deltas|) - sum(|negative deltas|) <= max_points_per_cycle
  - |delta_points| <= per_peer_cycle_cap
- On-chain checks on claim:
  - cycle exists with root
  - proof verifies
  - delta_points within [-per_peer_cycle_cap, per_peer_cycle_cap]
  - index not yet claimed in claims_bitmap
  - apply delta; clamp ledger points to >= 0

Instructions
1) initialize(governor, airdrop_recipient)
   - Creates GlobalConfig PDA with defaults.
   - Creates SEKA SPL Mint (decimals=6) and sets mint_authority to PDA ["mint_authority"].
   - Creates Treasury token account PDA for SEKA.
   - Mints 10,000 SEKA (10_000 * 10^6 units) to airdrop_recipient.
   - Emits event Initialized.

2) update_config(params)
   - Only governor.
   - Updatable: cycle_secs, max_points_per_cycle, per_peer_cycle_cap, conversion_ratio, join_cost_tokens, treasury.
   - Emits event ConfigUpdated.

3) set_cycle_root(cycle_index, merkle_root, total_points_declared, claims_bitmap_len)
   - Only governor.
   - total_points_declared <= max_points_per_cycle.
   - Initializes CycleState PDA for cycle_index with empty claims bitmap of given length.
   - Emits event CycleRootSet.

4) claim_karma(cycle_index, owner, delta_points, index, proof)
   - Verifies merkle proof against CycleState.merkle_root.
   - Ensures index is unclaimed; sets bit in claims_bitmap.
   - Ensures |delta_points| <= per_peer_cycle_cap.
   - Upserts PeerLedger for owner.
   - Applies delta: points = max(0, points + delta_points).
   - Updates PeerLedger.last_cycle_claimed = max(last, cycle_index).
   - Emits event KarmaClaimed.

5) convert_points_to_tokens(owner, max_points_to_convert, recipient_token_account)
   - Loads PeerLedger; computes convertible = floor(points / conversion_ratio) tokens.
   - Limits conversion to min(convertible, floor(max_points_to_convert / conversion_ratio)) if provided.
   - Deducts KP: points -= tokens * conversion_ratio.
   - Mints SEKA tokens to recipient ATA using mint_authority PDA.
   - Emits event PointsConverted.

6) join_network(member, payer_token_account)
   - Requires payer ATA contains >= join_cost_tokens.
   - Transfers join_cost_tokens from payer to Treasury PDA ATA.
   - Creates/activates Membership PDA for member.
   - Emits event Joined.

7) optional: deactivate_membership(member)
   - Governor-only or via governance flow; marks active=false (does not refund tokens).

Events (Anchor #[event])
- Initialized { governor, mint, treasury }
- ConfigUpdated { cycle_secs, max_points_per_cycle, per_peer_cycle_cap, conversion_ratio, join_cost_tokens }
- CycleRootSet { cycle_index, merkle_root, total_points_declared }
- KarmaClaimed { owner, cycle_index, delta_points, new_points }
- PointsConverted { owner, tokens_minted, points_spent }
- Joined { member }

Errors (examples)
- Unauthorized
- CycleAlreadyInitialized
- InvalidMerkleProof
- ClaimAlreadyProcessed
- DeltaExceedsPerPeerCap
- TotalPointsExceedsCycleCap (on set_cycle_root)
- InsufficientPointsToConvert
- InsufficientTokenBalance (join)

Derivation and Addressing
- GlobalConfig: PDA(seeds=[b"config"]).
- CycleState: PDA(seeds=[b"cycle", cycle_index.to_le_bytes()]).
- PeerLedger: PDA(seeds=[b"peer", owner]).
- Membership: PDA(seeds=[b"member", owner]).
- MintAuthority: PDA(seeds=[b"mint_authority"]).
- Treasury (ATA): Associated Token Account for GlobalConfig.treasury owner PDA with SEKA mint.

Schematics (ASCII)
Account topology:

  [Governor]
      |
      v
 [GlobalConfig PDA] --mint_authority--> [SEKA Mint]
      |                         \
      |                          \--> [Treasury ATA (PDA owner, SEKA)]
      |
      +--> [CycleState PDA(cycle=N)] --merkle_root--> [Off-chain merkle tree]
      |
      +--> [Membership PDA(owner=A)]
      |
      +--> [PeerLedger PDA(owner=A)]

Claim flow:

  Off-chain aggregator -> builds leaves (owner, cycle, delta, index) -> merkle_root
       |
   Governor set_cycle_root(cycle, root)
       |
  Peer A submit claim_karma(cycle, delta, index, proof)
       |
   Verify proof & caps
       |
   Mark bitmap[index]=1; update PeerLedger.points = max(0, points+delta)

Conversion flow:

  Peer A -> convert_points_to_tokens(max_points)
       |
   compute tokens = floor(points / conversion_ratio)
       |
   points -= tokens * conversion_ratio
       |
   mint SEKA to A's ATA (via mint_authority PDA)

Join flow:

  Peer A -> join_network(payer ATA)
       |
   transfer join_cost_tokens SEKA -> Treasury ATA
       |
   create Membership PDA(active=true)

Cycle and caps enforcement:
- Per-peer cap: enforced on claim (|delta_points| <= per_peer_cycle_cap).
- Cycle total cap: enforced on set_cycle_root via total_points_declared <= max_points_per_cycle.
- Negative deltas allowed; PeerLedger points are clamped at >= 0 after applying delta.

Integration points (off-chain)
- Scorer/monitor outputs per-cycle deltas; build Merkle tree and publish root + declared total.
- Gateway can query membership (Membership PDA exists and active) and KP/SEKA balances for tiering.
- Payment checks leverage SEKA token transfers on-chain; Gateway caches membership state.

Security & Auditing
- Governor must be a controlled authority (multisig or SPL Governance) to avoid unilateral abuse.
- set_cycle_root does not reveal all leaves on-chain; proofs reveal individual deltas on claim only.
- Claims use index and bitmap to prevent double-claim; include cycle_index in leaf to prevent replay.
- Mint authority is PDA; only conversion instruction can mint after init airdrop.
- Joining requires SEKA balance; tokens are transferred to Treasury PDA.

MVP Acceptance Criteria
- initialize creates config, mint, treasury; mints 10,000 SEKA to provided key.
- Governor can set root for a cycle within caps.
- Peers can claim KP once per leaf with valid proof; per-peer cap enforced.
- KP convert to SEKA at 100:1; balance accounting correct.
- Joining consumes 10 SEKA and creates active Membership.

Testing Plan (program level)
- Init flow test: config + mint + airdrop.
- Root lifecycle: set once, reject duplicates; caps enforced.
- Claim proofs: valid proof accepted; invalid rejected; double-claim prevented.
- Negative delta: clamp at 0 if points would go negative.
- Convert: exact multiples and remainders; decimals handling.
- Join: transfer amount correct; rejection on insufficient funds.

Build Notes
- Use Anchor account constraints for PDAs and token accounts.
- Use keccak or blake3 for Merkle hashing; document exact hashing function and leaf encoding in off-chain scorer.
- claims_bitmap sized to ceiling(num_leaves/8). For large cycles, consider chunking multiple bitmaps or using a compact bitset account.

Governance Roadmap
- Phase 1 (MVP): single Governor key or multisig.
- Phase 2: integrate with SPL Governance for proposals and parameter changes (join cost, caps, cycle secs).
- Phase 3: optional on-chain submission of likes/corroborations with stake-slashing (heavier footprint; off-chain remains preferred).

Parameter Defaults (initial)
- cycle_secs = 259200
- max_points_per_cycle = 10_000
- per_peer_cycle_cap = 100
- conversion_ratio = 100 (KP per SEKA)
- join_cost_tokens = 10 * 10^6 (with decimals=6)
- airdrop_on_init = 10_000 * 10^6 (to specified key)

Open Questions (for future iteration)
- Should negative deltas be allowed to push points below zero (debt)? MVP clamps at zero.
- Should join payments be burned instead of sent to treasury? MVP uses treasury for sustainability.
- How many decimals for SEKA? MVP uses 6; can be changed at init.
- Do we require membership for claiming? MVP: no; claim independent from membership.

Appendix — Example Leaf Serialization (canonical)
- Network byte order (LE for integers unless otherwise specified), using Anchor borsh-like encoding recommended.
- Leaf bytes = borsh_serialize({ owner: Pubkey(32), cycle_index: u64, delta_points: i32, index: u32 })
- Node hash = keccak256(left || right). Root is 32 bytes.
