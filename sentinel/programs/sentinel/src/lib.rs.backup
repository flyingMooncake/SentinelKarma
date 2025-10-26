use anchor_lang::prelude::*;
use anchor_lang::solana_program::clock::Clock;
use anchor_lang::solana_program::program_option::COption;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer, MintTo, SetAuthority};
use anchor_spl::associated_token::AssociatedToken;

// Bump seed constants
const STATE_SEED: &[u8] = b"state";
const TREASURY_VAULT_SEED: &[u8] = b"treasury";
const PEER_SEED: &[u8] = b"peer";
const POST_SEED: &[u8] = b"post";
const LIKE_SEED: &[u8] = b"like";

// Config constants
const SENTINEL_DECIMALS: u8 = 9; // standard SPL decimals
const JOIN_COST: u64 = 1_000 * 10u64.pow(SENTINEL_DECIMALS as u32);
const CYCLE_REWARD_TOTAL: u64 = 1_000 * 10u64.pow(SENTINEL_DECIMALS as u32);
const MAX_PEER_REWARD_PCT: u64 = 10; // 10%
const CYCLE_SECONDS: i64 = 2 * 60 * 60; // 2 hours
const INITIAL_MINT_SUPPLY: u64 = 100_000 * 10u64.pow(SENTINEL_DECIMALS as u32);

declare_id!("Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V");

#[program]
pub mod sentinel {
    use super::*;

    pub fn initialize(
        ctx: Context<Initialize>,
    ) -> Result<()> {
        let state = &mut ctx.accounts.state;
        state.authority = ctx.accounts.authority.key();
        state.sentinel_mint = ctx.accounts.sentinel_mint.key();
        state.treasury_vault = ctx.accounts.treasury_vault.key();
        state.cycle_start_ts = Clock::get()?.unix_timestamp;
        state.cycle_index = 0;

        // Mint initial supply to authority's ATA
        let cpi_ctx = CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.sentinel_mint.to_account_info(),
                to: ctx.accounts.authority_sentinel_ata.to_account_info(),
                authority: ctx.accounts.authority.to_account_info(),
            },
        );
        token::mint_to(cpi_ctx, INITIAL_MINT_SUPPLY)?;

        // hand off mint authority to state PDA for future rewards
        let cpi_ctx_set = CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            SetAuthority {
                account_or_mint: ctx.accounts.sentinel_mint.to_account_info(),
                current_authority: ctx.accounts.authority.to_account_info(),
            },
        );
        token::set_authority(
            cpi_ctx_set,
            anchor_spl::token::spl_token::instruction::AuthorityType::MintTokens,
            Some(ctx.accounts.state.key()),
        )?;

        Ok(())
    }

    pub fn join_network(ctx: Context<JoinNetwork>) -> Result<()> {
        // Transfer JOIN_COST from user to treasury vault
        let cpi_ctx = CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.user_sentinel_ata.to_account_info(),
                to: ctx.accounts.treasury_sentinel_ata.to_account_info(),
                authority: ctx.accounts.user.to_account_info(),
            },
        );
        token::transfer(cpi_ctx, JOIN_COST)?;

        // Activate peer state
        let peer = &mut ctx.accounts.peer;
        peer.user = ctx.accounts.user.key();
        peer.active = true;
        peer.karma = 0;
        // bump not stored

        Ok(())
    }

    pub fn mint_nft(ctx: Context<MintNft>, log_url: String, file_hash: [u8; 32]) -> Result<()> {
        require!(ctx.accounts.peer.active, SentinelError::NotPeer);
        require!(log_url.len() <= 200, SentinelError::UrlTooLong);

        // Mint the NFT (1 token of a new mint with 0 decimals) to user
        let cpi_ctx = CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.nft_mint.to_account_info(),
                to: ctx.accounts.user_nft_ata.to_account_info(),
                authority: ctx.accounts.user.to_account_info(),
            },
        );
        token::mint_to(cpi_ctx, 1)?;

        // Create post metadata
        let post = &mut ctx.accounts.post;
        post.owner = ctx.accounts.user.key();
        post.nft_mint = ctx.accounts.nft_mint.key();
        post.log_url = log_url;
        post.file_hash = file_hash;
        post.likes = 0;
        post.cycle_index = ctx.accounts.state.cycle_index;
        // bump not stored

        Ok(())
    }

    pub fn like_nft(ctx: Context<LikeNft>) -> Result<()> {
        // prevent double-like via PDA uniqueness and ensure liker is an active peer
        let post = &mut ctx.accounts.post;
        let liked_peer = &mut ctx.accounts.liked_peer;
        let liker_peer = &ctx.accounts.liker_peer;
        require!(liked_peer.active, SentinelError::NotPeer);
        require!(liker_peer.active, SentinelError::NotPeer);

        post.likes = post
            .likes
            .checked_add(1)
            .ok_or(SentinelError::Overflow)?;
        liked_peer.karma = liked_peer
            .karma
            .checked_add(1)
            .ok_or(SentinelError::Overflow)?;

        let like = &mut ctx.accounts.like;
        like.liker = ctx.accounts.liker.key();
        like.post = ctx.accounts.post.key();

        Ok(())
    }

    pub fn finalize_cycle<'info>(ctx: Context<'_, '_, '_, 'info, FinalizeCycle<'info>>, peers: Vec<Pubkey>, karmas: Vec<u64>) -> Result<()> {
        let now = Clock::get()?.unix_timestamp;
        require!(now - ctx.accounts.state.cycle_start_ts >= CYCLE_SECONDS, SentinelError::CycleNotEnded);
        require!(peers.len() == karmas.len(), SentinelError::InvalidInput);

        // Compute total karma
        let total_karma: u128 = karmas.iter().map(|k| *k as u128).sum();

        // Edge case: no karma -> nothing to distribute, just advance cycle
        if total_karma == 0 {
            ctx.accounts.state.cycle_start_ts = now;
            ctx.accounts.state.cycle_index = ctx.accounts.state.cycle_index.checked_add(1).ok_or(SentinelError::Overflow)?;
            return Ok(());
        }

        // Prepare signer seeds for state PDA mint authority (compute bump)
        let (_, state_bump) = Pubkey::find_program_address(&[STATE_SEED], &crate::ID);
        let signer_seeds: &[&[u8]] = &[STATE_SEED, &[state_bump]];
        let signer = &[signer_seeds];

        for (i, peer_pubkey) in peers.iter().enumerate() {
            let karma = karmas[i] as u128;
            if karma == 0 { continue; }
            // Proportional share
            let mut reward: u128 = (karma * CYCLE_REWARD_TOTAL as u128) / total_karma;
            // Cap at 10%
            let cap: u128 = (CYCLE_REWARD_TOTAL as u128 * MAX_PEER_REWARD_PCT as u128) / 100u128;
            if reward > cap { reward = cap; }
            let reward_u64: u64 = reward as u64;

            // Mint reward to peer's ATA passed in accounts via remaining_accounts mapping
            let ata_info = ctx.remaining_accounts.get(i).ok_or(SentinelError::MissingAccount)?;

            // Validate ATA is the canonical associated token address for (peer_pubkey, sentinel_mint)
            let expected_ata = anchor_spl::associated_token::get_associated_token_address(peer_pubkey, &ctx.accounts.sentinel_mint.key());
            require!(*ata_info.key == expected_ata, SentinelError::InvalidAccount);

            // Mint directly from sentinel mint with state as mint authority
            let cpi_ctx = CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                MintTo {
                    mint: ctx.accounts.sentinel_mint.to_account_info(),
                    to: ata_info.clone(),
                    authority: ctx.accounts.state.to_account_info(),
                },
            );
            token::mint_to(cpi_ctx.with_signer(signer), reward_u64)?;
        }

        // Reset karmas is delegated to off-chain indexing; keep on-chain simple to avoid huge loops updating many PDAs.
        // Advance cycle
        ctx.accounts.state.cycle_start_ts = now;
        ctx.accounts.state.cycle_index = ctx.accounts.state.cycle_index.checked_add(1).ok_or(SentinelError::Overflow)?;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,

    #[account(
        init,
        payer = authority,
        seeds = [STATE_SEED],
        bump,
        space = 8 + State::SIZE,
    )]
    pub state: Account<'info, State>,

    // Sentinel mint owned by state PDA as mint authority; created by authority
    #[account(
        init,
        payer = authority,
        mint::decimals = SENTINEL_DECIMALS,
        mint::authority = authority,
        mint::freeze_authority = state,
    )]
    pub sentinel_mint: Account<'info, Mint>,

    #[account(
        init,
        payer = authority,
        seeds = [TREASURY_VAULT_SEED],
        bump,
        space = 8 + TreasuryVault::SIZE,
    )]
    pub treasury_vault: Account<'info, TreasuryVault>,

    #[account(
        init,
        payer = authority,
        associated_token::mint = sentinel_mint,
        associated_token::authority = authority,
    )]
    pub authority_sentinel_ata: Account<'info, TokenAccount>,

    // Treasury vault ATA to hold JOIN fees
    #[account(
        init,
        payer = authority,
        associated_token::mint = sentinel_mint,
        associated_token::authority = treasury_vault,
    )]
    pub treasury_sentinel_ata: Account<'info, TokenAccount>,

    
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct JoinNetwork<'info> {
    #[account(mut)]
    pub user: Signer<'info>,

    pub state: Account<'info, State>,

    #[account(
        init,
        payer = user,
        seeds = [PEER_SEED, user.key().as_ref()],
        bump,
        space = 8 + PeerState::SIZE,
    )]
    pub peer: Account<'info, PeerState>,

    #[account(
        mut,
        constraint = user_sentinel_ata.mint == state.sentinel_mint,
        constraint = user_sentinel_ata.owner == user.key(),
    )]
    pub user_sentinel_ata: Account<'info, TokenAccount>,

    #[account(mut)]
    pub treasury_vault: Account<'info, TreasuryVault>,

    #[account(
        mut,
        constraint = treasury_sentinel_ata.mint == state.sentinel_mint,
        constraint = treasury_sentinel_ata.owner == treasury_vault.key(),
    )]
    pub treasury_sentinel_ata: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct MintNft<'info> {
    #[account(mut)]
    pub user: Signer<'info>,

    pub state: Account<'info, State>,

    #[account(
        mut,
        seeds = [PEER_SEED, user.key().as_ref()],
        bump,
        constraint = peer.user == user.key(),
    )]
    pub peer: Account<'info, PeerState>,

    // new NFT mint created ahead of time by client: must have 0 decimals & authority user
    #[account(
        mut,
        constraint = nft_mint.decimals == 0,
        constraint = nft_mint.mint_authority == COption::Some(user.key()),
    )]
    pub nft_mint: Account<'info, Mint>,

    #[account(
        init,
        payer = user,
        associated_token::mint = nft_mint,
        associated_token::authority = user,
    )]
    pub user_nft_ata: Account<'info, TokenAccount>,

    #[account(
        init,
        payer = user,
        seeds = [POST_SEED, nft_mint.key().as_ref()],
        bump,
        space = 8 + Post::SIZE,
    )]
    pub post: Account<'info, Post>,

    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct LikeNft<'info> {
    #[account(mut)]
    pub liker: Signer<'info>,

    pub state: Account<'info, State>,

    #[account(
        init,
        payer = liker,
        seeds = [LIKE_SEED, liker.key().as_ref(), post.key().as_ref()],
        bump,
        space = 8 + Like::SIZE,
    )]
    pub like: Account<'info, Like>,

    #[account(mut)]
    pub post: Account<'info, Post>,

    // Peer whose karma increases: the post owner
    #[account(
        mut,
        seeds = [PEER_SEED, post.owner.as_ref()],
        bump,
        constraint = liked_peer.user == post.owner,
    )]
    pub liked_peer: Account<'info, PeerState>,

    // Liker must also be an active peer
    #[account(
        seeds = [PEER_SEED, liker.key().as_ref()],
        bump,
        constraint = liker_peer.user == liker.key(),
        constraint = liker_peer.active,
    )]
    pub liker_peer: Account<'info, PeerState>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct FinalizeCycle<'info> {
    #[account(mut, address = state.authority)]
    pub authority: Signer<'info>,

    #[account(mut, seeds = [STATE_SEED], bump)]
    pub state: Account<'info, State>,

    #[account(mut)]
    pub sentinel_mint: Account<'info, Mint>,

    pub token_program: Program<'info, Token>,
}

#[account]
pub struct State {
    pub authority: Pubkey,
    pub sentinel_mint: Pubkey,
    pub treasury_vault: Pubkey,
    pub cycle_start_ts: i64,
    pub cycle_index: u64,
    }
impl State {
    pub const SIZE: usize = 112; // 32 + 32 + 32 + 8 + 8
}

#[account]
pub struct TreasuryVault {}
impl TreasuryVault {
    pub const SIZE: usize = 8; // minimal size for empty account
}

#[account]
pub struct PeerState {
    pub user: Pubkey,
    pub active: bool,
    pub karma: u64,
    }
impl PeerState {
    pub const SIZE: usize = 48; // 32 + 1 + 8 + padding
}

#[account]
pub struct Post {
    pub owner: Pubkey,
    pub nft_mint: Pubkey,
    pub log_url: String,        // HTTP URL to log file (max 200 chars)
    pub file_hash: [u8; 32],    // SHA256 hash of log file
    pub likes: u64,
    pub cycle_index: u64,
    }
impl Post {
    pub const SIZE: usize = 320; // 32 + 32 + (4 + 200) + 32 + 8 + 8
}

#[account]
pub struct Like {
    pub liker: Pubkey,
    pub post: Pubkey,
    }
impl Like {
    pub const SIZE: usize = 64; // 32 + 32
}

#[error_code]
pub enum SentinelError {
    #[msg("Math overflow")]
    Overflow,
    #[msg("User is not an active peer")]
    NotPeer,
    #[msg("Cycle not ended yet")]
    CycleNotEnded,
    #[msg("Invalid input vectors")]
    InvalidInput,
    #[msg("Missing remaining account for reward ATA")]
    MissingAccount,
    #[msg("Invalid account data")]
    InvalidAccount,
    #[msg("Log URL too long (max 200 characters)")]
    UrlTooLong,
}
