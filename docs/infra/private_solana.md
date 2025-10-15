# Private Solana Network — Setup Guide

Status: Practical guide (POC → multi-node)
Target Tooling: Solana 1.18.x, Anchor 0.30.x

Overview
This guide describes two ways to run a private Solana network:
- Single-node private network (POC/dev): solana-test-validator
- Multi-node private cluster: bootstrap validator + additional validators over an internal network

It also includes steps to deploy the SEKA program to your private network.

Prerequisites
- Linux host(s) with open ports on internal network
- Solana toolchain v1.18.x matching program deps
- Anchor CLI v0.30.x

Install Solana CLI
- curl -sSfL https://release.solana.com/v1.18.14/install | sh
- Add to PATH (usually ~/.local/share/solana/install/active_release/bin)

Check versions
- solana --version  # should be 1.18.x
- anchor --version  # should be 0.30.x

------------------------------------------------------------
Option 1: Single-node private network (POC)
------------------------------------------------------------
Run a local private validator with a persistent ledger. This network is entirely isolated; only clients you point at its RPC can connect.

1) Start the validator
- mkdir -p ./cluster/bootstrap-ledger
- solana-test-validator \
    --ledger ./cluster/bootstrap-ledger \
    --reset \
    --rpc-port 8899 \
    --faucet-port 9900 \
    --limit-ledger-size 500000000 \
    --slots-per-epoch 64

Notes
- The validator will not peer with public networks. It’s fully private by default.
- Restrict access: firewall RPC (8899) and faucet (9900) to your internal IP ranges.

2) Point Solana CLI to your private RPC
- solana config set --url http://127.0.0.1:8899

3) Fund a key (for deploys)
- solana-keygen new -o ./cluster/deployer.json
- solana airdrop 1000 $(solana-keygen pubkey ./cluster/deployer.json)
- solana balance --keypair ./cluster/deployer.json

4) Deploy SEKA program
- From repo root (this project):
  - anchor build
  - solana program deploy --keypair ./cluster/deployer.json target/deploy/seka.so
  - Record program id printed by deploy (update Anchor.toml/declare_id! if you want a permanent id)

5) Initialize SEKA config
- Create a recipient token account (ATA) for the airdrop recipient key.
- Use an Anchor script/test or ad-hoc client to call initialize(governor, airdrop_recipient, start_ts, decimals, airdrop_tokens):
  - governor: your deployer or multisig pubkey
  - airdrop_recipient: base58 pubkey
  - start_ts: current unix time
  - decimals: 6
  - airdrop_whole_tokens: 10000

6) Use your private network
- Clients and the gateway use RPC URL http://<host>:8899
- No public peering occurs; it’s a closed dev net.

------------------------------------------------------------
Option 2: Multi-node private cluster (internal network)
------------------------------------------------------------
Run a bootstrap validator as the cluster entrypoint and add additional validators that gossip only within your network.

Ports to plan (per validator)
- Gossip: 8001 (UDP/TCP)
- TPU (ingress): 8000
- JSON-RPC: 8899 (or unique per node; often only bootstrap exposes RPC)
- PubSub: 8900 (if enabled)
- Dynamic range: 8002-8020 (example)

Firewall baseline
- Block all ingress/egress to public internet for gossip/TPU.
- Allow gossip/TPU/RPC only among your node IPs.

A) Bootstrap validator
- Generate identity keys
  - solana-keygen new -o ./cluster/bootstrap/identity.json
- Create ledger
  - mkdir -p ./cluster/bootstrap/ledger
- Start bootstrap validator (no public bootstrap peers):
  solana-validator \
    --identity ./cluster/bootstrap/identity.json \
    --ledger ./cluster/bootstrap/ledger \
    --rpc-port 8899 \
    --gossip-port 8001 \
    --dynamic-port-range 8002-8020 \
    --no-untrusted-rpc \
    --entrypoint 0.0.0.0:8001 \
    --full-rpc-api \
    --private-rpc

Notes
- With no public entrypoints/bootstraps configured, the node forms a cluster of one.
- Restrict ports at firewall to internal networks only.
- You can use solana-test-validator instead if you don’t need multi-node functionality.

Find bootstrap info
- BOOTSTRAP_PUBKEY=$(solana-keygen pubkey ./cluster/bootstrap/identity.json)
- GENESIS_HASH=$(solana genesis-hash --ledger ./cluster/bootstrap/ledger)
- GOSSIP_ADDR=<bootstrap_private_ip>:8001

B) Additional validator(s)
- Generate identity:
  - solana-keygen new -o ./cluster/val1/identity.json
- Create ledger directory:
  - mkdir -p ./cluster/val1/ledger
- Start validator pointing to the bootstrap entrypoint and pinning genesis hash:
  solana-validator \
    --identity ./cluster/val1/identity.json \
    --ledger ./cluster/val1/ledger \
    --entrypoint ${GOSSIP_ADDR} \
    --known-validator ${BOOTSTRAP_PUBKEY} \
    --expected-genesis-hash ${GENESIS_HASH} \
    --gossip-port 8001 \
    --dynamic-port-range 8002-8020 \
    --no-untrusted-rpc \
    --no-wait-for-vote-to-start-leader \
    --wal-recovery-mode skip_any_corrupted_record

Notes
- Repeat for more validators; change ports or run behind separate hosts.
- Typically only the bootstrap exposes RPC; others can run with --no-rpc to reduce surface area.

C) A faucet (optional)
- For a private cluster, you can run a stand-alone faucet or rely on the bootstrap’s built-in faucet if using solana-test-validator.
- Stand-alone faucet example:
  solana-faucet --keypair ./cluster/bootstrap/identity.json --port 9900 --ip 0.0.0.0
- Restrict access to internal subnets.

D) Client configuration
- solana config set --url http://<bootstrap_ip>:8899

E) Deploy SEKA to the cluster
- anchor build
- solana program deploy target/deploy/seka.so
- Record the program ID; update Anchor.toml and declare_id! for permanence.

Hardening & Operations
- Time sync: run chrony/ntpd; clock drift impairs consensus.
- CPU/IO: validators are resource-intensive; provision SSDs (NVMe), many cores, high RAM.
- Snapshots: enable snapshot serving if you scale nodes; configure snapshot interval.
- Monitoring: enable metrics (Influx/Prometheus exporters), log aggregation.
- Backups: snapshot ledgers; keep keys offline and backed up securely.

Common tasks
- Check cluster health: solana-gossip spy --entrypoint <bootstrap_ip>:8001
- Get slot/epoch: solana slot, solana epoch-info
- Airdrop (if faucet available): solana airdrop 100 <pubkey>

Notes on program compatibility
- Program dependencies in this repo target solana-program 1.18.14; prefer Solana CLI/runtime 1.18.x.
- If you upgrade Solana, align Cargo.toml versions and re-build.

Deploying upgrades
- Update the program ID’s upgrade authority to your governance key.
- Use: solana program deploy --program-id <keypair.json> target/deploy/seka.so
- Or anchor deploy after setting Anchor.toml program id and wallet.

Appendix: Minimal single-node + Anchor deploy (quick commands)
- solana-test-validator --reset --ledger ./cluster/bootstrap-ledger &
- solana config set --url http://127.0.0.1:8899
- solana-keygen new -o ./cluster/deployer.json
- solana airdrop 1000 $(solana-keygen pubkey ./cluster/deployer.json)
- anchor build
- solana program deploy --keypair ./cluster/deployer.json target/deploy/seka.so

Security reminder
- A truly private network requires network-level controls: do not expose gossip/TPU/RPC to public internet; restrict to your nodes/IP ranges.
- Use separate keys for validator identity, deployer, and governance.
