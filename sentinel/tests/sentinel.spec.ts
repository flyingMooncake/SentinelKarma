import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { PublicKey, Keypair, SystemProgram, SYSVAR_RENT_PUBKEY } from "@solana/web3.js";
import {
  getAssociatedTokenAddressSync,
  createAssociatedTokenAccountInstruction,
  createTransferInstruction,
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
  createMint,
} from "@solana/spl-token";
import assert from "assert";

// Utility
const STATE_SEED = Buffer.from("state");
const TREASURY_SEED = Buffer.from("treasury");
const PEER_SEED = Buffer.from("peer");
const POST_SEED = Buffer.from("post");
const LIKE_SEED = Buffer.from("like");

const DECIMALS = 9n;
const LAMPORTS_PER_TOKEN = 10n ** DECIMALS;

describe("sentinel", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.Sentinel as Program<any>;

  const authority = provider.wallet as anchor.Wallet;

  let statePda: PublicKey;
  let treasuryPda: PublicKey;
  let sentinelMint: Keypair;
  let authoritySentinelAta: PublicKey;
  let treasurySentinelAta: PublicKey;

  it("initialize", async () => {
    [statePda] = PublicKey.findProgramAddressSync([STATE_SEED], program.programId);
    [treasuryPda] = PublicKey.findProgramAddressSync([TREASURY_SEED], program.programId);

    sentinelMint = Keypair.generate();
    authoritySentinelAta = getAssociatedTokenAddressSync(sentinelMint.publicKey, authority.publicKey);
    treasurySentinelAta = getAssociatedTokenAddressSync(sentinelMint.publicKey, treasuryPda, true);

    await program.methods
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

    // Check initial mint to authority
    const ataInfo = await provider.connection.getTokenAccountBalance(authoritySentinelAta);
    const amount = BigInt(ataInfo.value.amount);
    assert.equal(amount, 100_000n * LAMPORTS_PER_TOKEN);
  });

  it("join network: authority and a second peer", async () => {
    // Authority already has ATA with funds
    await program.methods
      .joinNetwork()
      .accounts({
        user: authority.publicKey,
        state: statePda,
        peer: PublicKey.findProgramAddressSync([PEER_SEED, authority.publicKey.toBuffer()], program.programId)[0],
        userSentinelAta: authoritySentinelAta,
        treasuryVault: treasuryPda,
        treasurySentinelAta: treasurySentinelAta,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    // Create second peer and fund with 1000 Sentinel
    const peerB = Keypair.generate();
    // Airdrop SOL to peerB
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(peerB.publicKey, 2 * anchor.web3.LAMPORTS_PER_SOL),
      "confirmed"
    );

    const peerBAta = getAssociatedTokenAddressSync(sentinelMint.publicKey, peerB.publicKey);

    // Create peerB ATA
    const createAtaIx = createAssociatedTokenAccountInstruction(
      authority.publicKey,
      peerBAta,
      peerB.publicKey,
      sentinelMint.publicKey,
      TOKEN_PROGRAM_ID,
      ASSOCIATED_TOKEN_PROGRAM_ID
    );

    // Transfer 1000 tokens from authority to peerB
    const transferIx = createTransferInstruction(
      authoritySentinelAta,
      peerBAta,
      authority.publicKey,
      Number(1000n * LAMPORTS_PER_TOKEN)
    );

    const tx = new anchor.web3.Transaction().add(createAtaIx, transferIx);
    await provider.sendAndConfirm(tx, []);

    // peerB joins
    await program.methods
      .joinNetwork()
      .accounts({
        user: peerB.publicKey,
        state: statePda,
        peer: PublicKey.findProgramAddressSync([PEER_SEED, peerB.publicKey.toBuffer()], program.programId)[0],
        userSentinelAta: peerBAta,
        treasuryVault: treasuryPda,
        treasurySentinelAta: treasurySentinelAta,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .signers([peerB])
      .rpc();
  });

  it("mint NFT and like it", async () => {
    // Use authority as NFT minter (peer A)
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

    const postPda = PublicKey.findProgramAddressSync([
      POST_SEED,
      nftMint.toBuffer(),
    ], program.programId)[0];

    const hash32 = new Array(32).fill(0);
    await program.methods
      .mintNft(hash32, treasuryPda)
      .accounts({
        user: authority.publicKey,
        state: statePda,
        peer: PublicKey.findProgramAddressSync([PEER_SEED, authority.publicKey.toBuffer()], program.programId)[0],
        nftMint,
        userNftAta,
        post: postPda,
        tokenProgram: TOKEN_PROGRAM_ID,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        rent: SYSVAR_RENT_PUBKEY,
      })
      .rpc();

    // Like from peerB
    const peerB = Keypair.generate();
    await provider.connection.confirmTransaction(
      await provider.connection.requestAirdrop(peerB.publicKey, 1 * anchor.web3.LAMPORTS_PER_SOL),
      "confirmed"
    );

    // Re-derive peerB peer and expect it already exists from previous test would not in a new test context
    // For demo, create minimal LikeNft context by funding and joining peerB again here

    // Transfer 1000 tokens to peerB and join
    const peerBAta = getAssociatedTokenAddressSync(sentinelMint.publicKey, peerB.publicKey);
    const createPeerBAtaIx = createAssociatedTokenAccountInstruction(
      authority.publicKey,
      peerBAta,
      peerB.publicKey,
      sentinelMint.publicKey
    );
    const transferToPeerBIx = createTransferInstruction(
      authoritySentinelAta,
      peerBAta,
      authority.publicKey,
      Number(1000n * LAMPORTS_PER_TOKEN)
    );
    await provider.sendAndConfirm(new anchor.web3.Transaction().add(createPeerBAtaIx, transferToPeerBIx));

    await program.methods
      .joinNetwork()
      .accounts({
        user: peerB.publicKey,
        state: statePda,
        peer: PublicKey.findProgramAddressSync([PEER_SEED, peerB.publicKey.toBuffer()], program.programId)[0],
        userSentinelAta: peerBAta,
        treasuryVault: treasuryPda,
        treasurySentinelAta: treasurySentinelAta,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .signers([peerB])
      .rpc();

    const likedPeerPda = PublicKey.findProgramAddressSync([PEER_SEED, authority.publicKey.toBuffer()], program.programId)[0];
    const likerPeerPda = PublicKey.findProgramAddressSync([PEER_SEED, peerB.publicKey.toBuffer()], program.programId)[0];
    const likePda = PublicKey.findProgramAddressSync([LIKE_SEED, peerB.publicKey.toBuffer(), postPda.toBuffer()], program.programId)[0];

    await program.methods
      .likeNft()
      .accounts({
        liker: peerB.publicKey,
        state: statePda,
        like: likePda,
        post: postPda,
        likedPeer: likedPeerPda,
        likerPeer: likerPeerPda,
        systemProgram: SystemProgram.programId,
      })
      .signers([peerB])
      .rpc();

    const postAcc: any = await program.account.post.fetch(postPda);
    assert.equal(Number(postAcc.likes), 1);

    const likedPeerAcc: any = await program.account.peerState.fetch(likedPeerPda);
    assert.equal(Number(likedPeerAcc.karma), 1);
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
      assert.fail("expected error");
    } catch (e: any) {
      const msg = e.error?.errorMessage || e.message || "";
      assert(msg.includes("Cycle not ended yet"));
    }
  });
});
