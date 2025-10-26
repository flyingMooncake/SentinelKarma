const anchor = require("@coral-xyz/anchor");
const { PublicKey, Keypair, SystemProgram } = require("@solana/web3.js");
const {
  getAssociatedTokenAddressSync,
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
  createMint,
} = require("@solana/spl-token");
const fs = require("fs");
const os = require("os");

// Load IDL
const idl = require("./target/idl/sentinel.json");

const PROGRAM_ID = new PublicKey("7e5HppSuDGkqSjgKNfC62saPoJR5LBkYMuQHkv59eDY7");

async function main() {
  console.log("🧪 Testing Sentinel Contract");
  console.log("============================\n");

  // Setup provider
  const connection = new anchor.web3.Connection("http://localhost:8899", "confirmed");
  
  // Load wallet
  const walletPath = `${os.homedir()}/.config/solana/id.json`;
  const walletKeypair = Keypair.fromSecretKey(
    Buffer.from(JSON.parse(fs.readFileSync(walletPath, "utf-8")))
  );
  const wallet = new anchor.Wallet(walletKeypair);
  
  const provider = new anchor.AnchorProvider(connection, wallet, {
    commitment: "confirmed",
  });
  anchor.setProvider(provider);
  
  const program = new anchor.Program(idl, PROGRAM_ID, provider);
  const authority = provider.wallet;

  console.log("📍 Program ID:", PROGRAM_ID.toString());
  console.log("👤 Wallet:", authority.publicKey.toString());
  console.log("");

  // Derive PDAs
  const [statePda] = PublicKey.findProgramAddressSync(
    [Buffer.from("state")],
    PROGRAM_ID
  );
  
  const [treasuryPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("treasury")],
    PROGRAM_ID
  );

  console.log("🔑 State PDA:", statePda.toString());
  console.log("🔑 Treasury PDA:", treasuryPda.toString());
  console.log("");

  try {
    // Step 1: Check if program is initialized
    console.log("1️⃣ Checking if program is initialized...");
    try {
      const stateAccount = await program.account.state.fetch(statePda);
      console.log("✅ Program already initialized");
      console.log("   Authority:", stateAccount.authority.toString());
      console.log("   Sentinel Mint:", stateAccount.sentinelMint.toString());
      console.log("   Cycle Index:", stateAccount.cycleIndex.toString());
      console.log("");
    } catch (e) {
      console.log("⚠️  Program not initialized yet");
      console.log("   You need to run the initialize instruction first");
      console.log("   See: anchor test --skip-local-validator");
      console.log("");
      return;
    }

    // Step 2: Check if user has joined network
    console.log("2️⃣ Checking if user has joined network...");
    const [peerPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("peer"), authority.publicKey.toBuffer()],
      PROGRAM_ID
    );
    
    try {
      const peerAccount = await program.account.peerState.fetch(peerPda);
      console.log("✅ User is a network member");
      console.log("   Active:", peerAccount.active);
      console.log("   Karma:", peerAccount.karma.toString());
      console.log("");
    } catch (e) {
      console.log("⚠️  User has not joined network yet");
      console.log("   You need to call join_network first");
      console.log("");
      return;
    }

    // Step 3: Mint NFT
    console.log("3️⃣ Minting NFT...");
    
    // Get state to get sentinel mint
    const stateAccount = await program.account.state.fetch(statePda);
    
    // Create NFT mint (0 decimals)
    console.log("   Creating NFT mint...");
    const nftMint = await createMint(
      provider.connection,
      authority.payer,
      authority.publicKey,
      null,
      0, // 0 decimals for NFT
      undefined,
      undefined,
      TOKEN_PROGRAM_ID
    );
    console.log("   NFT Mint:", nftMint.toString());

    const userNftAta = getAssociatedTokenAddressSync(
      nftMint,
      authority.publicKey
    );

    const [postPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("post"), nftMint.toBuffer()],
      PROGRAM_ID
    );

    // Create hash and db_addr (NEW SIGNATURE!)
    const hash = Array(32).fill(0); // 32-byte hash
    hash[0] = 1; // Make it unique
    const dbAddr = Keypair.generate().publicKey; // Database address

    console.log("   Calling mint_nft instruction...");
    const tx = await program.methods
      .mintNft(hash, dbAddr) // ✅ NEW SIGNATURE: (hash, db_addr)
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
        rent: anchor.web3.SYSVAR_RENT_PUBKEY,
      })
      .rpc();

    console.log("✅ NFT minted successfully!");
    console.log("   Transaction:", tx);
    console.log("   Post PDA:", postPda.toString());
    console.log("");

    // Verify post was created
    const postAccount = await program.account.post.fetch(postPda);
    console.log("📄 Post Details:");
    console.log("   Owner:", postAccount.owner.toString());
    console.log("   NFT Mint:", postAccount.nftMint.toString());
    console.log("   Hash:", Buffer.from(postAccount.hash).toString('hex').substring(0, 16) + "...");
    console.log("   DB Address:", postAccount.dbAddr.toString());
    console.log("   Likes:", postAccount.likes.toString());
    console.log("   Cycle Index:", postAccount.cycleIndex.toString());
    console.log("");

    console.log("🎉 Test completed successfully!");

  } catch (error) {
    console.error("❌ Error:", error.message);
    if (error.logs) {
      console.error("\nProgram Logs:");
      error.logs.forEach(log => console.error("  ", log));
    }
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
