# SEKA Testing Network (Docker)

This Docker Compose stack runs a private single-node Solana network using solana-test-validator.

Alternative: you can also start a local validator without Docker using the repo manager:
- ./manager.sh --local_network
- This starts solana-test-validator on the host (127.0.0.1:8899, faucet 9900) and validates local blocks. See details below.

What you get
- Isolated Solana RPC at localhost:8899
- Local faucet at localhost:9900
- Persistent ledger on ./ledger

Prerequisites
- Docker and Docker Compose plugin

Usage
- Start the network:
  docker compose up -d

- Check health:
  docker compose ps

- View logs:
  docker compose logs -f solana

- Stop:
  docker compose down

- Reset ledger (wipe chain state):
  docker compose down -v && rm -rf ledger && docker compose up -d

Point Solana CLI to the testing network (host CLI)
- solana config set --url http://127.0.0.1:8899

Use Solana CLI from inside the container (optional)
- docker compose exec solana solana config set --url http://localhost:8899
- docker compose exec solana solana --version

Create a deployer key and airdrop funds (host CLI)
- solana-keygen new -o ./infra/testing_network/deployer.json
- solana airdrop 1000 $(solana-keygen pubkey ./infra/testing_network/deployer.json)

Deploy the SEKA program (from repository root)
- anchor build
- solana program deploy --keypair ./infra/testing_network/deployer.json target/deploy/seka.so

Manager integration (non-Docker local validator)
- Start local validator on the host:
  ./manager.sh --local_network
- If tmux is installed, the validator runs in session "seka-localnet" (attach with: tmux attach -t seka-localnet)
- Logs (non-tmux path): infra/testing_network/solana.log; PID: infra/testing_network/solana.pid
- Important: Do not run both the Docker validator and the host validator at the same time (both use 8899/9900). Stop one before starting the other.

Notes
- The test-validator is started with --full-rpc-api and --private-rpc for local-only development.
- Exposed ports are only bound on localhost by default via Docker bridge; secure accordingly if running on a server.
