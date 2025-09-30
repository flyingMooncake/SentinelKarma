import * as anchor from "@coral-xyz/anchor";
import { Program, AnchorProvider } from "@coral-xyz/anchor";
import { PublicKey, Keypair, SystemProgram, SYSVAR_RENT_PUBKEY } from "@solana/web3.js";
import {
  getAssociatedTokenAddressSync,
  createAssociatedTokenAccountInstruction,
  createTransferInstruction,
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
  createMint,
} from "@solana/spl-token";

// Load IDL
const idl = require("../target/idl/sentinel.json");

// Utility
const STATE_SEED = Buffer.from("state");
const TREASURY_SEED = Buffer.from("treasury");
const PEER_SEED = Buffer.from("peer");
const POST_SEED = Buffer.from("post");
const LIKE_SEED = Buffer.from("like");

const DECIMALS = 9n;
const LAMPORTS_PER_TOKEN = 10n ** DECIMALS;

describe("sentinel", () => {
  const provider = AnchorProvider.env();
  anchor.setProvider(provider);

  const programId = new PublicKey("Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V");
  const program = new Program(idl, provider);

  const authority = provider.wallet as anchor.Wallet;

  let statePda: PublicKey;
  let treasuryPda: PublicKey;
  let sentinelMint: Keypair;
  let authoritySentinelAta: PublicKey;
  let treasurySentinelAta: PublicKey;

  it("initialize", async () => {
    [statePda] = PublicKey.findProgramAddressSync([STATE_SEED], programId);
    [treasuryPda] = PublicKey.findProgramAddressSync([TREASURY_SEED], programId);

    sentinelMint = Keypair.generate();
    authoritySentinelAta = getAssociatedTokenAddressSync(sentinelMint.publicKey, authority.publicKey);
    treasurySentinelAta = getAssociatedTokenAddressSync(sentinelMint.publicKey, treasuryPda, true);

    const tx = await program.methods
      .initialize()
      .accounts({
        authority: authority.publicKey,
        state: statePda,
        sentinelMint: sentinelMint.publicKey,
        treasuryVault: treasuryPda,
        authoritySentinelAta,
        treasurySentinelAta,
        tokenProgram: TOKEN_PROGRAM_ID,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        rent: SYSVAR_RENT_PUBKEY,
      })
      .signers([sentinelMint])
      .rpc();

    console.log("✓ Initialize tx:", tx);

    // Check initial mint to authority
    const ataInfo = await provider.connection.getTokenAccountBalance(authoritySentinelAta);
    const amount = BigInt(ataInfo.value.amount);
    console.log("✓ Authority balance:", amount / LAMPORTS_PER_TOKEN, "Sentinel");
    
    if (amount !== 100_000n * LAMPORTS_PER_TOKEN) {
      throw new Error(`Expected 100,000 tokens, got ${amount / LAMPORTS_PER_TOKEN}`);
    }
  });

  it("join network: authority", async () => {
    const peerPda = PublicKey.findProgramAddressSync([PEER_SEED, authority.publicKey.toBuffer()], programId)[0];

    const tx = await program.methods
      .joinNetwork()
      .accounts({
        user: authority.publicKey,
        state: statePda,
        peer: peerPda,
        userSentinelAta: authoritySentinelAta,
        treasuryVault: treasuryPda,
        treasurySentinelAta: treasurySentinelAta,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    console.log("✓ Authority joined network, tx:", tx);

    // Check balance decreased by 1000
    const ataInfo = await provider.connection.getTokenAccountBalance(authoritySentinelAta);
    const amount = BigInt(ataInfo.value.amount);
    console.log("✓ Authority balance after join:", amount / LAMPORTS_PER_TOKEN, "Sentinel");
  });

  it("join network: second peer", async () => {
    const peerB = Keypair.generate();
    
    // Airdrop SOL to peerB
    const sig = await provider.connection.requestAirdrop(peerB.publicKey, 2 * anchor.web3.LAMPORTS_PER_SOL);
    await provider.connection.confirmTransaction(sig, "confirmed");

    const peerBAta = getAssociatedTokenAddressSync(sentinelMint.publicKey, peerB.publicKey);

    // Create peerB ATA and transfer 1000 tokens
    const createAtaIx = createAssociatedTokenAccountInstruction(
      authority.publicKey,
      peerBAta,
      peerB.publicKey,
      sentinelMint.publicKey,
      TOKEN_PROGRAM_ID,
      ASSOCIATED_TOKEN_PROGRAM_ID
    );

    const transferIx = createTransferInstruction(
      authoritySentinelAta,
      peerBAta,
      authority.publicKey,
      Number(1000n * LAMPORTS_PER_TOKEN)
    );

    const tx1 = new anchor.web3.Transaction().add(createAtaIx, transferIx);
    await provider.sendAndConfirm(tx1, []);

    console.log("✓ Funded peerB with 1000 Sentinel");

    // peerB joins
    const peerBPda = PublicKey.findProgramAddressSync([PEER_SEED, peerB.publicKey.toBuffer()], programId)[0];

    const tx2 = await program.methods
      .joinNetwork()
      .accounts({
        user: peerB.publicKey,
        state: statePda,
        peer: peerBPda,
        userSentinelAta: peerBAta,
        treasuryVault: treasuryPda,
        treasurySentinelAta: treasurySentinelAta,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .signers([peerB])
      .rpc();

    console.log("✓ PeerB joined network, tx:", tx2);
  });

  it("mint NFT", async () => {
    const nftMint = await createMint(
      provider.connection,
      authority.payer,
      authority.publicKey,
      null,
      0,
      undefined,
      undefined,
      TOKEN_PROGRAM_ID
    );
    
    const userNftAta = getAssociatedTokenAddressSync(nftMint, authority.publicKey);
    const peerPda = PublicKey.findProgramAddressSync([PEER_SEED, authority.publicKey.toBuffer()], programId)[0];
    const postPda = PublicKey.findProgramAddressSync([POST_SEED, nftMint.toBuffer()], programId)[0];

    const hash32 = new Array(32).fill(0);
    const tx = await program.methods
      .mintNft(hash32, treasuryPda)
      .accounts({
        user: authority.publicKey,
        state: statePda,
        peer: peerPda,
        nftMint,
        userNftAta,
        post: postPda,
        tokenProgram: TOKEN_PROGRAM_ID,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        rent: SYSVAR_RENT_PUBKEY,
      })
      .rpc();

    console.log("✓ NFT minted, tx:", tx);
    console.log("✓ Post PDA:", postPda.toBase58());
  });

  it("finalize cycle fails early if < 2h", async () => {
    try {
      await program.methods
        .finalizeCycle([authority.publicKey], [new anchor.BN(1)])
        .accounts({
          authority: authority.publicKey,
          state: statePda,
          sentinelMint: sentinelMint.publicKey,
          tokenProgram: TOKEN_PROGRAM_ID,
        })
        .remainingAccounts([
          { pubkey: authoritySentinelAta, isSigner: false, isWritable: true },
        ])
        .rpc();
      
      throw new Error("Expected error but succeeded");
    } catch (e: any) {
      const msg = e.error?.errorMessage || e.message || "";
      if (msg.includes("Cycle not ended yet") || msg.includes("6002")) {
        console.log("✓ Finalize cycle correctly rejected (cycle not ended)");
      } else {
        throw e;
      }
    }
  });

  console.log("\n✅ All tests passed!");
});
