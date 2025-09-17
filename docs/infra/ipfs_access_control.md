# Private IPFS Access with SEKA Membership Authentication

Status: Design Spec (MVP)

Goal
- Make IPFS artifacts (logs, manifests) accessible only to nodes in a private network and only after a client proves ownership of a key that is registered in the on-chain SEKA membership contract.
- The client sends a signed message that includes the requested CID (hash) to retrieve. The gateway verifies on-chain membership and serves the content.

Overview
- Storage: IPFS private network (swarm key). Nodes not in the swarm cannot fetch content.
- Access gate: HTTP gateway service (co-located with IPFS node) verifies Solana signatures from membership keys.
- Authorization: CID must be part of the allowed set (derived from cycle manifests/NFT metadata).
- Delivery: Gateway streams the content from the local IPFS node after successful auth or returns a short-lived one-time token.

Components
- IPFS Kubo (private network): stores and serves content only to swarm peers.
- Gateway (FastAPI from the plan): provides endpoints to request access using signed messages and streams from IPFS.
- On-chain SEKA Program: membership PDA existence and active=true required (join paid in SEKA).
- Content Index: gateway-maintained list of allowed CIDs (from manifests uploaded each cycle to IPFS/Arweave).

Private IPFS Network
- Generate a swarm key and deploy Kubo with the key on all participating nodes.
- Disable public network features and expose API only to localhost.

Steps
1) Generate swarm key on a trusted machine:
   - Use ipfs-swarm-key-gen or equivalent to create a 32-byte pre-shared key file named swarm.key
   - Distribute securely to all nodes; do not commit to VCS.

2) Kubo config (config.yaml or via env):
   - Place swarm.key in the IPFS repo directory (e.g., ~/.ipfs/swarm.key)
   - API.ListenMultiaddr: 127.0.0.1:5001 (local only)
   - Gateway disabled or behind the HTTP gateway service
   - Routing.Type: dhtclient (private) or none; relays disabled
   - Bootstrap: only your internal bootstrap peers

3) Docker example (snippet):
   version: '3.8'
   services:
     ipfs:
       image: ipfs/kubo:latest
       restart: unless-stopped
       ports:
         - '4001:4001/tcp'
         - '4001:4001/udp'
         - '127.0.0.1:5001:5001'
       volumes:
         - ./ipfs/data:/data/ipfs
         - ./ipfs/swarm.key:/data/ipfs/swarm.key:ro
       environment:
         - IPFS_PROFILE=server

Authorization Model
- A client must prove control of a registered membership key by signing a specific message that includes the target CID.
- The gateway verifies the signature and membership before serving or issuing a one-time token.

Canonical Signed Message
- String to sign (newline-delimited; exact key order):
  SEKA-IPFS-REQ\n
  cid:<CIDv1>\n
  exp:<unix_ts>\n
  nonce:<base58-16-bytes>\n
  program:<seka_program_id>\n
  cluster:<cluster_id>

- Rules:
  - cid: CIDv1 string (ipfs add --cid-version=1)
  - exp: expiration unix timestamp (UTC) within 60–300 seconds from now
  - nonce: 16 random bytes, base58-encoded; single-use per pubkey
  - program: on-chain program id for SEKA
  - cluster: 'devnet' | 'testnet' | 'mainnet-beta' | 'localnet'

- Signature: ed25519 over UTF-8 bytes of the string above using the Solana keypair.
- Signature transport encoding: base58.

Gateway API (augmenting the existing gateway)
- POST /ipfs/request
  - Body: { pubkey: <base58>, cid: <string>, exp: <u64>, nonce: <string>, signature: <base58>, cluster?: <string> }
  - Steps:
    1) Verify signature with pubkey over canonical message.
    2) Check exp within clock skew, and nonce is unused (store for TTL ~5 min).
    3) Verify membership: load Membership PDA (seeds ["member", pubkey]) from SEKA program; ensure active=true.
    4) Authorize CID: ensure cid is in the allowed set (pre-indexed from cycle manifests/NFT metadata).
    5) Rate-limit by membership tier if applicable.
    6a) Stream: immediately fetch and stream from local IPFS (default for POC), or
    6b) Token: return { token, expires_at } where token is a signed, one-time JWT with claims { sub: pubkey, cid, exp }.

- GET /ipfs/get?cid=<cid>&token=<jwt> (only if 6b chosen)
  - Verifies JWT signature and exp, then streams the content from IPFS to the client.

CID Authorization Source
- The gateway maintains a CID allowlist sourced from the cycle manifests:
  - For each cycle: manifest JSON includes the list of files and their CIDs.
  - The gateway ingests new manifests (from IPFS or Arweave) and updates the allowlist.
  - Optionally also ingest NFT metadata to cross-validate CIDs.

Streaming Implementation (POC)
- Use IPFS HTTP API locally (127.0.0.1:5001) to fetch:
  - /api/v0/cat?arg=<cid> for raw files
  - Stream bytes to client with appropriate Content-Type (e.g., application/gzip) and Content-Length if available.
- Add simple content-type mapping by filename extension from the manifest.

Security Considerations
- Private swarm ensures only your nodes participate in the DHT and data transfer.
- Gateway is the only external interface; IPFS API is local-only.
- Nonce cache prevents replay within the token lifetime.
- CID allowlist prevents arbitrary IPFS access.
- Clock skew tolerance: ±30s; exp max 5m from now.
- Audit logs: record pubkey, cid, time, size, and outcome per request.

Membership Check (SEKA Program)
- PDA: seeds=["member", owner_pubkey]
- Fields: { owner: Pubkey, joined_at: i64, active: bool }
- Gateway validates active==true.

Tiering (optional)
- Use points or tiers from the karma system to limit bandwidth or history depth.
- Enforce per-pubkey rate limiting (token bucket) and per-IP safeguards.

POC / Localnet Setup
- Start local IPFS with swarm.key and no public bootstrap nodes.
- Run gateway on the same host; configure SEKA program id and cluster=localnet.
- Client flow:
  1) Client constructs canonical string with cid/exp/nonce and signs with their Solana keypair.
  2) POST /ipfs/request with pubkey, cid, exp, nonce, signature.
  3) Gateway verifies and streams the content.

Operational Notes
- Rotate swarm.key only with coordinated downtime (all nodes must share it).
- For redundancy, deploy two gateway+IPFS nodes behind an internal load balancer.
- For scale, layer in caching (filesystem or CDN) keyed by cid and membership tier.

Telemetry & Monitoring
- Expose counters: requests by outcome, bytes served, latency, cache hit rate, auth failures.
- Log request id with pubkey, cid, and correlation id for audit.

Future Enhancements
- Add /ipfs/presign to return one-time tokens and support distributed proxies.
- Store minted cNFT asset id per cycle on-chain in SEKA program for discoverability.
- Add signing domain separator with gateway instance id to prevent cross-gateway replay.
- Mutual TLS within the private network to secure IPFS peer connections further.
