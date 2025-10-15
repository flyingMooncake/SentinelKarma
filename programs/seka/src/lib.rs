use anchor_lang::prelude::*;
use anchor_lang::solana_program::keccak::hashv;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{self, Mint, MintTo, Token, TokenAccount, Transfer};

declare_id!("SEKA111111111111111111111111111111111111111");

const DEFAULT_DECIMALS: u8 = 6;
const DEFAULT_CYCLE_SECS: u64 = 259_200; // 3 days
const DEFAULT_MAX_POINTS_PER_CYCLE: u32 = 10_000;
const DEFAULT_PER_PEER_CYCLE_CAP: i32 = 100;
const DEFAULT_CONVERSION_RATIO: u32 = 100; // KP per 1 SEKA

#[program]
pub mod seka {
    use super::*;

    pub fn initialize(
        ctx: Context<Initialize>,
        governor: Pubkey,
        airdrop_recipient: Pubkey,
        start_ts: i64,
        decimals: u8,
        airdrop_whole_tokens: u64, // e.g., 10_000 for 10k SEKA
    ) -> Result<()> {
        let cfg = &mut ctx.accounts.config;
        cfg.bump = *ctx.bumps.get("config").unwrap();
        cfg.governor = governor;
        cfg.treasury = ctx.accounts.treasury_pda.key();
        cfg.mint = ctx.accounts.mint.key();
        cfg.mint_authority = ctx.accounts.mint_authority_pda.key();
        cfg.cycle_secs = DEFAULT_CYCLE_SECS;
        cfg.max_points_per_cycle = DEFAULT_MAX_POINTS_PER_CYCLE;
        cfg.per_peer_cycle_cap = DEFAULT_PER_PEER_CYCLE_CAP;
        cfg.conversion_ratio = DEFAULT_CONVERSION_RATIO;
        cfg.join_cost_tokens = 10u64 * pow10(decimals as u32);
        cfg.start_ts = start_ts;
        cfg.airdrop_done = false;
        cfg.decimals = decimals;

        // Create the recipient ATA if not exists (optional best-effort)
        // Expect recipient_ata to be provided or created externally.
        let base_units = airdrop_whole_tokens
            .checked_mul(pow10(decimals as u32))
            .ok_or(ErrorCode::MathOverflow)?;

        // Mint airdrop to recipient ATA using mint_authority PDA.
        let seeds: &[&[u8]] = &[b"mint_authority", &[*ctx.bumps.get("mint_authority_pda").unwrap()]];
        let signer_seeds: &[&[&[u8]]] = &[seeds];
        let cpi_ctx = CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.mint.to_account_info(),
                to: ctx.accounts.airdrop_recipient_ata.to_account_info(),
                authority: ctx.accounts.mint_authority_pda.to_account_info(),
            },
            signer_seeds,
        );
        token::mint_to(cpi_ctx, base_units)?;

        cfg.airdrop_done = true;
        emit!(Initialized {
            governor,
            mint: cfg.mint,
            treasury: ctx.accounts.treasury_ata.key(),
        });
        Ok(())
    }

    pub fn update_config(ctx: Context<UpdateConfig>, params: UpdateParams) -> Result<()> {
        let cfg = &mut ctx.accounts.config;
        require_keys_eq!(ctx.accounts.signer.key(), cfg.governor, ErrorCode::Unauthorized);

        if let Some(v) = params.cycle_secs { cfg.cycle_secs = v; }
        if let Some(v) = params.max_points_per_cycle { cfg.max_points_per_cycle = v; }
        if let Some(v) = params.per_peer_cycle_cap { cfg.per_peer_cycle_cap = v; }
        if let Some(v) = params.conversion_ratio { cfg.conversion_ratio = v; }
        if let Some(v) = params.join_cost_tokens { cfg.join_cost_tokens = v; }
        if let Some(v) = params.treasury_owner {
            cfg.treasury = v;
        }
        emit!(ConfigUpdated {
            cycle_secs: cfg.cycle_secs,
            max_points_per_cycle: cfg.max_points_per_cycle,
            per_peer_cycle_cap: cfg.per_peer_cycle_cap,
            conversion_ratio: cfg.conversion_ratio,
            join_cost_tokens: cfg.join_cost_tokens,
        });
        Ok(())
    }

    pub fn set_cycle_root(
        ctx: Context<SetCycleRoot>,
        cycle_index: u64,
        merkle_root: [u8; 32],
        total_points_declared: u32,
        claims_bitmap_len: u32,
    ) -> Result<()> {
        let cfg = &ctx.accounts.config;
        require_keys_eq!(ctx.accounts.signer.key(), cfg.governor, ErrorCode::Unauthorized);
        require!(total_points_declared <= cfg.max_points_per_cycle, ErrorCode::TotalPointsExceedsCycleCap);

        let state = &mut ctx.accounts.cycle_state;
        state.bump = *ctx.bumps.get("cycle_state").unwrap();
        state.cycle_index = cycle_index;
        state.merkle_root = merkle_root;
        state.total_points_declared = total_points_declared;
        state.claims_bitmap = vec![0u8; claims_bitmap_len as usize];

        emit!(CycleRootSet { cycle_index, merkle_root, total_points_declared });
        Ok(())
    }

    pub fn claim_karma(
        ctx: Context<ClaimKarma>,
        owner: Pubkey,
        cycle_index: u64,
        delta_points: i32,
        leaf_index: u32,
        proof: Vec<[u8; 32]>,
    ) -> Result<()> {
        let cfg = &ctx.accounts.config;
        let state = &mut ctx.accounts.cycle_state;
        require!(state.cycle_index == cycle_index, ErrorCode::InvalidCycle);
        require!(delta_points.abs() as i32 <= cfg.per_peer_cycle_cap, ErrorCode::DeltaExceedsPerPeerCap);

        // Reconstruct leaf and verify Merkle proof using positional path from leaf_index bits.
        let leaf_bytes = serialize_leaf(&owner, cycle_index, delta_points, leaf_index);
        let leaf_hash = keccak_hash(&leaf_bytes);
        let computed_root = compute_merkle_root(leaf_hash, &proof, leaf_index);
        require!(computed_root == state.merkle_root, ErrorCode::InvalidMerkleProof);

        // Check and set claim bit
        require!(!is_claimed(&state.claims_bitmap, leaf_index), ErrorCode::ClaimAlreadyProcessed);
        set_claimed(&mut state.claims_bitmap, leaf_index)?;

        // Upsert PeerLedger and apply delta with clamp to >= 0
        let ledger = &mut ctx.accounts.ledger;
        if ledger.owner == Pubkey::default() {
            ledger.bump = *ctx.bumps.get("ledger").unwrap();
            ledger.owner = owner;
            ledger.points = 0;
            ledger.last_cycle_claimed = 0;
        } else {
            require_keys_eq!(ledger.owner, owner, ErrorCode::WrongLedgerOwner);
        }

        let new_points = if delta_points >= 0 {
            ledger.points.checked_add(delta_points as i64).ok_or(ErrorCode::MathOverflow)?
        } else {
            let dp = (-delta_points) as i64;
            ledger.points.saturating_sub(dp)
        };
        ledger.points = new_points;
        if cycle_index > ledger.last_cycle_claimed { ledger.last_cycle_claimed = cycle_index; }

        emit!(KarmaClaimed { owner, cycle_index, delta_points, new_points });
        Ok(())
    }

    pub fn convert_points_to_tokens(
        ctx: Context<ConvertPointsToTokens>,
        owner: Pubkey,
        tokens_to_mint_whole: u64, // whole SEKA tokens, not base units
    ) -> Result<()> {
        let cfg = &ctx.accounts.config;
        let ledger = &mut ctx.accounts.ledger;
        require_keys_eq!(ledger.owner, owner, ErrorCode::WrongLedgerOwner);

        let needed_points = (tokens_to_mint_whole as i64)
            .checked_mul(cfg.conversion_ratio as i64)
            .ok_or(ErrorCode::MathOverflow)?;
        let convertible_tokens = (ledger.points as i64) / (cfg.conversion_ratio as i64);
        require!(tokens_to_mint_whole as i64 <= convertible_tokens, ErrorCode::InsufficientPointsToConvert);

        ledger.points = ledger
            .points
            .checked_sub(needed_points)
            .ok_or(ErrorCode::MathOverflow)?;

        let base_units = tokens_to_mint_whole
            .checked_mul(pow10(cfg.decimals as u32))
            .ok_or(ErrorCode::MathOverflow)?;

        let seeds: &[&[u8]] = &[b"mint_authority", &[*ctx.bumps.get("mint_authority_pda").unwrap()]];
        let signer_seeds: &[&[&[u8]]] = &[seeds];
        let cpi_ctx = CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.mint.to_account_info(),
                to: ctx.accounts.recipient_ata.to_account_info(),
                authority: ctx.accounts.mint_authority_pda.to_account_info(),
            },
            signer_seeds,
        );
        token::mint_to(cpi_ctx, base_units)?;

        emit!(PointsConverted { owner, tokens_minted: tokens_to_mint_whole, points_spent: needed_points as u64 });
        Ok(())
    }

    pub fn join_network(ctx: Context<JoinNetwork>, member: Pubkey) -> Result<()> {
        let cfg = &ctx.accounts.config;
        // Transfer join_cost_tokens from payer to treasury ATA.
        let cpi_ctx = CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.payer_ata.to_account_info(),
                to: ctx.accounts.treasury_ata.to_account_info(),
                authority: ctx.accounts.payer.to_account_info(),
            },
        );
        token::transfer(cpi_ctx, cfg.join_cost_tokens)?;

        // Activate membership
        let m = &mut ctx.accounts.membership;
        if m.owner == Pubkey::default() {
            m.bump = *ctx.bumps.get("membership").unwrap();
            m.owner = member;
        } else {
            require_keys_eq!(m.owner, member, ErrorCode::WrongMembershipOwner);
        }
        m.active = true;
        m.joined_at = Clock::get()?.unix_timestamp;

        emit!(Joined { member });
        Ok(())
    }

    pub fn deactivate_membership(ctx: Context<DeactivateMembership>, member: Pubkey) -> Result<()> {
        let cfg = &ctx.accounts.config;
        require_keys_eq!(ctx.accounts.signer.key(), cfg.governor, ErrorCode::Unauthorized);
        let m = &mut ctx.accounts.membership;
        require_keys_eq!(m.owner, member, ErrorCode::WrongMembershipOwner);
        m.active = false;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = GlobalConfig::SPACE,
        seeds = [b"config"],
        bump,
    )]
    pub config: Account<'info, GlobalConfig>,

    #[account(
        init,
        payer = payer,
        mint::decimals = DEFAULT_DECIMALS,
        mint::authority = mint_authority_pda,
        mint::freeze_authority = mint_authority_pda,
    )]
    pub mint: Account<'info, Mint>,

    /// PDA used as the mint authority
    /// CHECK: PDA signer via seeds
    #[account(seeds = [b"mint_authority"], bump)]
    pub mint_authority_pda: UncheckedAccount<'info>,

    /// PDA that owns the treasury ATA
    /// CHECK: PDA only
    #[account(seeds = [b"treasury"], bump)]
    pub treasury_pda: UncheckedAccount<'info>,

    #[account(
        init,
        payer = payer,
        associated_token::mint = mint,
        associated_token::authority = treasury_pda,
    )]
    pub treasury_ata: Account<'info, TokenAccount>,

    /// Recipient ATA for initial airdrop; must be associated to the provided recipient
    #[account(mut)]
    pub airdrop_recipient_ata: Account<'info, TokenAccount>,

    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Default)]
pub struct UpdateParams {
    pub cycle_secs: Option<u64>,
    pub max_points_per_cycle: Option<u32>,
    pub per_peer_cycle_cap: Option<i32>,
    pub conversion_ratio: Option<u32>,
    pub join_cost_tokens: Option<u64>, // base units
    pub treasury_owner: Option<Pubkey>,
}

#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    #[account(mut, seeds = [b"config"], bump = config.bump)]
    pub config: Account<'info, GlobalConfig>,
    pub signer: Signer<'info>,
}

#[derive(Accounts)]
pub struct SetCycleRoot<'info> {
    pub signer: Signer<'info>,
    pub system_program: Program<'info, System>,
    #[account(mut, seeds = [b"config"], bump = config.bump)]
    pub config: Account<'info, GlobalConfig>,
    #[account(
        init,
        payer = signer,
        space = CycleState::space_for(0), // will reallocate below using vec of desired len
        seeds = [b"cycle", cycle_index_le(&cycle_index)],
        bump,
    )]
    pub cycle_state: Account<'info, CycleState>,
}

#[derive(Accounts)]
pub struct ClaimKarma<'info> {
    #[account(mut, seeds = [b"config"], bump = config.bump)]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut, seeds = [b"cycle", cycle_index_le(&cycle_state.cycle_index)], bump = cycle_state.bump)]
    pub cycle_state: Account<'info, CycleState>,
    #[account(
        init_if_needed,
        payer = payer,
        space = PeerLedger::SPACE,
        seeds = [b"peer", owner.as_ref()],
        bump,
    )]
    pub ledger: Account<'info, PeerLedger>,
    /// Payer for rent if ledger is created
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ConvertPointsToTokens<'info> {
    #[account(mut, seeds = [b"config"], bump = config.bump)]
    pub config: Account<'info, GlobalConfig>,
    #[account(mut, seeds = [b"peer", owner.as_ref()], bump = ledger.bump)]
    pub ledger: Account<'info, PeerLedger>,
    #[account(mut)]
    pub mint: Account<'info, Mint>,
    /// CHECK: PDA signer for mint
    #[account(seeds = [b"mint_authority"], bump)]
    pub mint_authority_pda: UncheckedAccount<'info>,
    #[account(mut)]
    pub recipient_ata: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct JoinNetwork<'info> {
    #[account(mut, seeds = [b"config"], bump = config.bump)]
    pub config: Account<'info, GlobalConfig>,
    /// CHECK: treasury owner PDA
    #[account(seeds = [b"treasury"], bump)]
    pub treasury_pda: UncheckedAccount<'info>,
    #[account(mut)]
    pub treasury_ata: Account<'info, TokenAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(mut, constraint = payer_ata.owner == payer.key(), constraint = payer_ata.mint == config.mint)]
    pub payer_ata: Account<'info, TokenAccount>,
    #[account(
        init_if_needed,
        payer = payer,
        space = Membership::SPACE,
        seeds = [b"member", member.as_ref()],
        bump,
    )]
    pub membership: Account<'info, Membership>,
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct DeactivateMembership<'info> {
    #[account(mut, seeds = [b"config"], bump = config.bump)]
    pub config: Account<'info, GlobalConfig>,
    pub signer: Signer<'info>,
    #[account(mut, seeds = [b"member", member.as_ref()], bump = membership.bump)]
    pub membership: Account<'info, Membership>,
}

#[account]
pub struct GlobalConfig {
    pub bump: u8,
    pub governor: Pubkey,
    pub treasury: Pubkey,
    pub mint: Pubkey,
    pub mint_authority: Pubkey,
    pub cycle_secs: u64,
    pub max_points_per_cycle: u32,
    pub per_peer_cycle_cap: i32,
    pub conversion_ratio: u32,
    pub join_cost_tokens: u64, // base units (decimals)
    pub start_ts: i64,
    pub airdrop_done: bool,
    pub decimals: u8,
}
impl GlobalConfig {
    pub const SPACE: usize = 8 /*disc*/ + 1 + 32 + 32 + 32 + 32 + 8 + 4 + 4 + 4 + 8 + 8 + 1 + 1 + 16; // pad
}

#[account]
pub struct CycleState {
    pub bump: u8,
    pub cycle_index: u64,
    pub merkle_root: [u8; 32],
    pub total_points_declared: u32,
    pub claims_bitmap: Vec<u8>,
}
impl CycleState {
    pub fn space_for(bitmap_len: u32) -> usize {
        8 /*disc*/ + 1 + 8 + 32 + 4 + 4 /*vec prefix*/ + bitmap_len as usize + 16
    }
}

#[account]
pub struct PeerLedger {
    pub bump: u8,
    pub owner: Pubkey,
    pub points: i64,
    pub last_cycle_claimed: u64,
}
impl PeerLedger {
    pub const SPACE: usize = 8 /*disc*/ + 1 + 32 + 8 + 8 + 16;
}

#[account]
pub struct Membership {
    pub bump: u8,
    pub owner: Pubkey,
    pub joined_at: i64,
    pub active: bool,
}
impl Membership {
    pub const SPACE: usize = 8 /*disc*/ + 1 + 32 + 8 + 1 + 16;
}

#[event]
pub struct Initialized {
    pub governor: Pubkey,
    pub mint: Pubkey,
    pub treasury: Pubkey,
}

#[event]
pub struct ConfigUpdated {
    pub cycle_secs: u64,
    pub max_points_per_cycle: u32,
    pub per_peer_cycle_cap: i32,
    pub conversion_ratio: u32,
    pub join_cost_tokens: u64,
}

#[event]
pub struct CycleRootSet {
    pub cycle_index: u64,
    pub merkle_root: [u8; 32],
    pub total_points_declared: u32,
}

#[event]
pub struct KarmaClaimed {
    pub owner: Pubkey,
    pub cycle_index: u64,
    pub delta_points: i32,
    pub new_points: i64,
}

#[event]
pub struct PointsConverted {
    pub owner: Pubkey,
    pub tokens_minted: u64,
    pub points_spent: u64,
}

#[event]
pub struct Joined {
    pub member: Pubkey,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Unauthorized")] Unauthorized,
    #[msg("Cycle already initialized")] CycleAlreadyInitialized,
    #[msg("Invalid Merkle proof")] InvalidMerkleProof,
    #[msg("Claim already processed")] ClaimAlreadyProcessed,
    #[msg("Delta exceeds per-peer cap")] DeltaExceedsPerPeerCap,
    #[msg("Total points exceed cycle cap")] TotalPointsExceedsCycleCap,
    #[msg("Insufficient points to convert")] InsufficientPointsToConvert,
    #[msg("Insufficient token balance")] InsufficientTokenBalance,
    #[msg("Math overflow")] MathOverflow,
    #[msg("Invalid cycle")] InvalidCycle,
    #[msg("Wrong ledger owner")] WrongLedgerOwner,
    #[msg("Wrong membership owner")] WrongMembershipOwner,
}

fn cycle_index_le(idx: &u64) -> [u8; 8] { idx.to_le_bytes() }

fn pow10(p: u32) -> u64 { 10u64.pow(p) }

fn serialize_leaf(owner: &Pubkey, cycle_index: u64, delta_points: i32, leaf_index: u32) -> Vec<u8> {
    let mut v = Vec::with_capacity(32 + 8 + 4 + 4);
    v.extend_from_slice(owner.as_ref());
    v.extend_from_slice(&cycle_index.to_le_bytes());
    v.extend_from_slice(&delta_points.to_le_bytes());
    v.extend_from_slice(&leaf_index.to_le_bytes());
    v
}

fn keccak_hash(data: &[u8]) -> [u8; 32] { hashv(&[data]).0 }

fn compute_merkle_root(mut leaf: [u8; 32], proof: &Vec<[u8; 32]>, leaf_index: u32) -> [u8; 32] {
    let mut idx = leaf_index;
    let mut hash = leaf;
    for sibling in proof.iter() {
        let (left, right) = if idx & 1 == 1 {
            (sibling, &hash)
        } else {
            (&hash, sibling)
        };
        let combined = [left.as_slice(), right.as_slice()].concat();
        hash = keccak_hash(&combined);
        idx >>= 1;
    }
    hash
}

fn is_claimed(bitmap: &Vec<u8>, index: u32) -> bool {
    let byte_index = (index / 8) as usize;
    let bit_index = (index % 8) as u8;
    if byte_index >= bitmap.len() { return false; }
    (bitmap[byte_index] & (1u8 << bit_index)) != 0
}

fn set_claimed(bitmap: &mut Vec<u8>, index: u32) -> Result<()> {
    let byte_index = (index / 8) as usize;
    let bit_index = (index % 8) as u8;
    require!(byte_index < bitmap.len(), ErrorCode::InvalidMerkleProof);
    bitmap[byte_index] |= 1u8 << bit_index;
    Ok(())
}
