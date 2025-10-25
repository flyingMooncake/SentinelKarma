/**
 * TypeScript types for Sentinel NFT minting
 * Matches the on-chain Post account structure
 */

import { PublicKey } from '@solana/web3.js';

/**
 * Input data required for minting an NFT
 */
export interface MintNftInput {
  /** HTTP URL to the log file (max 200 characters) */
  log_url: string;
  
  /** SHA256 hash of the log file (32 bytes / 64 hex chars) */
  file_hash: string;
}

/**
 * On-chain Post account data structure
 */
export interface PostAccount {
  /** Owner's public key */
  owner: PublicKey;
  
  /** NFT mint address */
  nft_mint: PublicKey;
  
  /** HTTP URL to log file (max 200 chars) */
  log_url: string;
  
  /** SHA256 hash of log file (32 bytes) */
  file_hash: Uint8Array;
  
  /** Number of likes */
  likes: bigint;
  
  /** Cycle index when posted */
  cycle_index: bigint;
}

/**
 * Complete mint transaction data
 */
export interface MintTransaction {
  /** User's public key (signer) */
  user: PublicKey;
  
  /** NFT mint address (created beforehand) */
  nft_mint: PublicKey;
  
  /** Log URL to store on-chain */
  log_url: string;
  
  /** File hash to store on-chain */
  file_hash: Uint8Array;
}

/**
 * Helper to convert hex string to byte array
 */
export function hexToBytes(hex: string): Uint8Array {
  if (hex.length !== 64) {
    throw new Error('Hash must be 64 hex characters (32 bytes)');
  }
  
  const bytes = new Uint8Array(32);
  for (let i = 0; i < 32; i++) {
    bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return bytes;
}

/**
 * Helper to convert byte array to hex string
 */
export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Validate mint input data
 */
export function validateMintInput(input: MintNftInput): boolean {
  // Check URL length
  if (input.log_url.length > 200) {
    throw new Error('URL too long (max 200 characters)');
  }
  
  // Check URL format
  if (!input.log_url.startsWith('http://') && !input.log_url.startsWith('https://')) {
    throw new Error('URL must start with http:// or https://');
  }
  
  // Check hash format
  if (!/^[a-fA-F0-9]{64}$/.test(input.file_hash)) {
    throw new Error('Hash must be 64 hex characters');
  }
  
  return true;
}

/**
 * Example mint data
 */
export const EXAMPLE_MINT_DATA: MintNftInput = {
  log_url: 'http://172.19.12.161:9000/logs/ed2336ded3a9213a',
  file_hash: 'ed2336ded3a9213a3aa1f7a0a563527a5549d243b0970e482e257bc374b72cd6'
};

/**
 * Account sizes (in bytes)
 */
export const ACCOUNT_SIZES = {
  State: 112,      // 32 + 32 + 32 + 8 + 8
  PeerState: 48,   // 32 + 1 + 8 + padding
  Post: 320,       // 32 + 32 + (4 + 200) + 32 + 8 + 8
  Like: 64,        // 32 + 32
  TreasuryVault: 8 // minimal
};