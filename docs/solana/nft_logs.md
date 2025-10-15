# NFT-based Log Archiving — Decentralized Storage Design

Status: Design Spec (MVP)
Chosen Stack: Arweave (via Irys/Bundlr) for storage + Metaplex Compressed NFTs (Bubblegum) for indexing

Objective
- Persist each report/log artifact to decentralized storage.
- Publish an NFT per cycle (or per report, configurable) where the NFT metadata contains:
  - Canonical links (URIs) to the archived log files and a manifest.
  - Integrity data (sha256) and cycle identifiers.
  - Optional gateway deep links for convenience.

Why Arweave + cNFT
- Arweave provides permanent storage with strong content addressing and wide NFT tooling support.
- Irys/Bundlr allows paying in SOL and batching uploads efficiently.
- Metaplex Compressed NFTs (cNFT) are low-cost, scalable on Solana, with content URIs pointing to Arweave.
- This minimizes on-chain footprint while giving immutable, auditable references to logs.

Scope
- Off-chain pipeline uploads:
  - Log artifact(s) — e.g., malicious logs and contract_data for a cycle.
  - Cycle manifest JSON with size and sha256 per file.
  - NFT metadata JSON referencing the above.
- On-chain mint:
  - Create a cNFT per cycle with metadata_uri set to the uploaded Arweave metadata JSON.
- Optional linkage to the karma program:
  - Include CycleState.merkle_root and cycle_index inside NFT attributes for cryptographic association with on-chain state.

Granularity
- Default: 1 NFT per cycle, containing URIs to all artifacts of that cycle.
- Optional: 1 NFT per report (more NFTs, finer indexing). The pipeline supports both; choose via config.

Artifacts and Metadata
1) Log files (recommend gzip compression):
   - logs/malicious_<cycle_index>.jsonl.gz
   - contract_data/cd_<cycle_index>.json.gz

2) Cycle manifest JSON (Arweave): manifest_<cycle_index>.json
   {
     "v": 1,
     "cycle_index": <u64>,
     "time": { "start": <unix>, "end": <unix> },
     "files": [
       { "name": "malicious_<cycle>.jsonl.gz", "uri": "ar://<txid>", "sha256": "<hex>", "size": <bytes>, "mime": "application/gzip" },
       { "name": "cd_<cycle>.json.gz", "uri": "ar://<txid>", "sha256": "<hex>", "size": <bytes>, "mime": "application/gzip" }
     ],
     "merkle_root": "0x<32-byte-hex>",
     "declared_points": <u32>
   }

3) NFT metadata JSON (Arweave): meta_<cycle_index>.json
   {
     "name": "Sentinel Cycle #<cycle_index>",
     "symbol": "SEKA-CYCLE",
     "description": "Immutable archive of SentinelKarma logs for cycle <cycle_index>.",
     "image": "https://arweave.net/<optional-static-image>",
     "external_url": "https://gateway.example/windows/<cycle_index>",
     "attributes": [
       { "trait_type": "cycle_index", "value": <u64> },
       { "trait_type": "merkle_root", "value": "0x<32-byte-hex>" },
       { "trait_type": "declared_points", "value": <u32> },
       { "trait_type": "start_ts", "value": <unix> },
       { "trait_type": "end_ts", "value": <unix> }
     ],
     "properties": {
       "category": "application",
       "files": [
         { "uri": "ar://<log_txid>", "type": "application/gzip", "sha256": "<hex>", "name": "malicious_<cycle>.jsonl.gz" },
         { "uri": "ar://<cd_txid>", "type": "application/gzip", "sha256": "<hex>", "name": "cd_<cycle>.json.gz" },
         { "uri": "ar://<manifest_txid>", "type": "application/json", "sha256": "<hex>", "name": "manifest_<cycle>.json" }
       ]
     }
   }

Security and Integrity
- Compute sha256 for each uploaded file and place in both manifest and NFT metadata.
- Store CycleState.merkle_root (from the karma program) in NFT attributes for verifiable association.
- Use immutable Arweave transactions; avoid mutable gateways for URIs (prefer ar:// or https://arweave.net/).

On-chain Considerations
- No changes to the existing karma Anchor program required for MVP.
- Optionally, add a governor-only instruction record_cycle_asset(cycle_index, asset_id) to store the cNFT asset id in CycleState for on-chain discoverability. This is not required if off-chain indexers are used.

Minting Strategy
- Use Metaplex Bubblegum (compressed NFTs) to minimize cost at scale:
  - Create a Merkle tree once and keep its authority under the Governor multisig/key.
  - Mint one cNFT per cycle with metadata_uri = ar://<meta_txid>.
  - Set seller_fee_basis_points = 0 and transferability as per policy (typically transferable; can be non-transferable if desired via custom rulesets).
- Alternatively, mint standard NFTs (Token Metadata) if cNFT infra is not available; this is more expensive.

Off-chain Pipeline (CLI outline)
1) Prepare inputs
   - cycle_index, t_start, t_end, declared_points, merkle_root
   - paths to local log files for the cycle (gzip recommended)

2) Upload files to Arweave via Irys
   - Use @irys/sdk (Bundlr) with SOL funding
   - Upload each file with tags: Content-Type, cycle_index, kind
   - Capture txids

3) Upload manifest JSON
   - Construct manifest with txids and sha256 values
   - Upload to Arweave; obtain manifest_txid

4) Upload NFT metadata JSON
   - Construct metadata referencing the file txids and manifest
   - Upload to Arweave; obtain metadata_txid

5) Mint cNFT
   - Use Metaplex Umi + Bubblegum to mint compressed NFT with URI = ar://metadata_txid
   - Authority: Governor/publisher key
   - Optionally call record_cycle_asset(cycle_index, asset_id) on the karma program if implemented

6) Publish summary
   - Post cycle summary (cycle_index, arweave URIs, asset_id) to a public JSON index (e.g., in gateway) for easy discovery

Example Commands (pseudo)
- Hashing:
  sha256sum malicious_123.jsonl.gz > malicious_123.jsonl.gz.sha256

- Node: Irys upload (JS)
  const irys = new Irys({ network: 'https://node1.irys.xyz', token: 'solana' })
  await irys.fund(1e9) // 1 SOL in lamports equivalent for funding
  const txLog = await irys.uploadFile('malicious_123.jsonl.gz', { tags: [{ name: 'Content-Type', value: 'application/gzip' }, { name: 'cycle_index', value: '123' }, { name: 'kind', value: 'malicious' }] })
  const txCd  = await irys.uploadFile('cd_123.json.gz',        { tags: [{ name: 'Content-Type', value: 'application/gzip' }, { name: 'cycle_index', value: '123' }, { name: 'kind', value: 'contract_data' }] })
  const txMan = await irys.upload(JSON.stringify(manifest), { tags: [{ name: 'Content-Type', value: 'application/json' }, { name: 'cycle_index', value: '123' }, { name: 'kind', value: 'manifest' }] })
  const txMeta= await irys.upload(JSON.stringify(nftMeta),  { tags: [{ name: 'Content-Type', value: 'application/json' }, { name: 'cycle_index', value: '123' }, { name: 'kind', value: 'nft_metadata' }] })

- Mint compressed NFT (JS/TS, Umi + Bubblegum)
  const umi = createUmi('https://api.mainnet-beta.solana.com').use(mplBubblegum())
  const tree = publicKey('<bubblegum_tree_pubkey>')
  await mintToCollectionV1(umi, { tree, metadata: { uri: `ar://${txMeta.id}`, name: `Sentinel Cycle #123`, symbol: 'SEKA-CYCLE', sellerFeeBasisPoints: percentAmount(0) }, leafOwner: publicKey('<publisher_or_treasury>') }).sendAndConfirm(umi)

Data Retention & Discoverability
- Arweave ensures permanence; cNFTs act as decentralized indexes to the content.
- Gateway may expose a simple /cycles/<index> endpoint that redirects to Arweave metadata and files.
- Optionally mirror metadata JSON to IPFS for redundancy (list multiple URIs in properties.files).

Costs (rough)
- Arweave: depends on bytes; gzip and compact schema reduce cost significantly.
- Irys funding: SOL balance required; automated top-up recommended.
- cNFT: very low mint fees compared to standard NFTs.

Operational Policies
- Publisher authority (Governor) signs uploads and mints.
- Rotate/segregate keys for upload vs mint if preferred.
- Rate-limit publication to one NFT per cycle; re-upload only on failure; do not mutate.

Testing Checklist
- Upload and verify txids resolve on arweave.net
- Validate sha256 of downloaded files equals recorded hashes
- Mint cNFT and confirm URI resolves to metadata JSON with valid structure
- (Optional) record asset_id in karma program and read back for the cycle

Future Enhancements
- Add per-report NFTs if community wants finer granularity; link them to cycle NFT via attributes.
- Include a second storage URI (IPFS) in properties.files for multi-network redundancy.
- Implement record_cycle_asset(cycle_index, asset_id) in the Anchor program for on-chain discoverability.
- Add a simple explorer page in the gateway to browse cycles and open Arweave files.
