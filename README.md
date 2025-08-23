# SentinelKarma v0.1 — Developer Documentation (MVP)

> **What**: Telemetry + anti-abuse MVP for Web3/RPC networks  
> **How**: Reads JSONL events → computes p95, error-rate, z-scores → publishes diagnostics over MQTT → splits to `malicious_logs/` vs `logs_normal/` with rotation  
> **Test**: Synthetic traffic generator with bursts

---

## Repository Layout

```
SentinelKarma/
├── agent-python/
│   ├── Dockerfile
│   ├── agent/
│   │   └── main.py               # metrics agent (MQTT publisher)
│   └── tools/
│       └── generator.py          # synthetic event generator
├── data/
│   ├── rpc.jsonl                 # source event stream (generator output)
│   ├── malicious_logs/           # rotated “malicious” windows
│   └── logs_normal/              # rotated normal windows
├── docker-compose.yml            # mosquitto, agent, generator, saver
├── mosquitto.conf                # broker config (listener 0.0.0.0:1883)
└── manager.sh                    # helper CLI (check/start/test/overburst/…)
```

---

## Services

### Mosquitto (MQTT broker)
- **Image:** `eclipse-mosquitto:2`  
- **Port:** `1883`
- **Config (`mosquitto.conf`):**
  ```conf
  listener 1883 0.0.0.0
  allow_anonymous true
  persistence false
  log_type all
  ```
- **Healthcheck (compose):**
  ```yaml
  healthcheck:
    test: ["CMD-SHELL", "mosquitto_sub -h localhost -t '$$SYS/broker/uptime' -C 1 -W 3 || exit 1"]
    interval: 5s
    timeout: 3s
    retries: 5
  ```

### Agent (metrics + publisher)
- **Entrypoint:** `python -m agent.main`
- **Input:** `/data/rpc.jsonl` (JSONL events)  
- **Window:** `WINDOW_MS` ms (rolling)
- **Outputs (published to MQTT topic, default `sentinel/diag`):**
  ```json
  {
    "ts": 1755944583,
    "window_ms": 250,
    "region": "eu-central",
    "asn": 64512,
    "method": "getLogs",
    "metrics": { "p95": 274.41, "err_rate": 0.0 },
    "z": { "lat": 12.53, "err": 0.0 },
    "sample": "iphash:44f8aab55b43"
  }
  ```
- **Env (compose example):**
  ```yaml
  agent:
    build: ./agent-python
    image: sentinelkarma-agent
    container_name: sentinel-agent
    restart: unless-stopped
    environment:
      MQTT_HOST: mosquitto
      MQTT_PORT: "1883"
      MQTT_TOPIC: sentinel/diag
      LOG_PATH: /data/rpc.jsonl
      REGION: eu-central
      ASN: "64512"
      WINDOW_MS: "250"
      Z_THRESHOLD: "3.0"
      METHODS_HEAVY: getProgramAccounts,getLogs
      SALT: change-me
    volumes:
      - ./data:/data
    depends_on:
      mosquitto:
        condition: service_healthy
  ```

### Generator (synthetic traffic)
- **Entrypoint:** `python -m tools.generator`
- **Writes:** `/data/rpc.jsonl`
- **Useful flags:**
  ```bash
  python -m tools.generator \
    --log /data/rpc.jsonl \
    --rate 2000 \
    --burst getProgramAccounts \
    --err 0.7 \
    --baseline_lat 220 \
    --burst_lat 480 \
    --burst_secs 60
  ```

### Saver / Collector (split + rotation)
- **Subscribes:** `sentinel/diag` via `mosquitto_sub`
- **Classifies to files using thresholds (see below)**
- **Rotation:**
  - `malicious_logs/`: every `MAL_WINDOW_MIN` minutes
  - `logs_normal/`: every `NOR_WINDOW_MIN` minutes

> **Tip (file ownership):**  
> In repo root create `.env` with local IDs:
> ```bash
> printf "UID=%s\nGID=%s\n" "$(id -u)" "$(id -g)" > .env
> ```
> and set on saver service:
> ```yaml
> user: "${UID}:${GID}"
> ```

---

## Runtime Thresholds & Rotation

Environment variables read by `manager.sh`/saver:

```bash
# classification thresholds
ERR_THR=0.05     # min error-rate to flag malicious (0..1)
ZLAT_THR=4       # latency z-score threshold
ZERR_THR=2       # error-rate z-score threshold
P95_THR=250      # p95 latency threshold (ms)

# rotation
MAL_WINDOW_MIN=3   # rotate malicious files every N minutes
NOR_WINDOW_MIN=30  # rotate normal files every N minutes
```

A message goes to `malicious_logs/` if **any**:
- `metrics.err_rate >= ERR_THR`
- `metrics.p95 >= P95_THR`
- `z.lat >= ZLAT_THR`
- `z.err >= ZERR_THR`  
Else it goes to `logs_normal/`.

---

## Manager CLI (`manager.sh`)

**Flags**
- `--help` — show help
- `--check` — detect missing tools (docker, compose plugin, jq, mosquitto_sub, etc.)
- `--install` — apt-based install of prereqs (best effort; WSL-friendly)
- `--docker` — build images / prepare compose (no run)
- `--start` — start **mosquitto + agent + generator + saver** in background  
  - `--verbose` (optional): stream broker logs
- `--test` — start stack + open live tails (uses tmux fallback if no gnome-terminal)
- `--overburst` — trigger a strong synthetic burst (detached generator)
- `--stop` — stop background services
- `--docker-purge` — remove images/volumes
- `--docker-reinstall` — purge + rebuild

**Overburst knobs (env)**

```bash
OVER_RATE=2000
OVER_ERR=0.7
OVER_BASE_LAT=220
OVER_BURST_LAT=480
OVER_SECS=60
```

---

## Quick Start

```bash
# From repo root
./manager.sh --check
sudo ./manager.sh --install      # optional

# Start stack
./manager.sh --start

# Synthetic stress + file split/rotation validation
./manager.sh --overburst

# Broker sanity (short peek)
docker compose exec -T mosquitto sh -lc \
  "timeout 5s mosquitto_sub -h localhost -t 'sentinel/#' -v | head -20"

# Inspect latest files
ls -lAh data/malicious_logs | tail -n 5
ls -lAh data/logs_normal   | tail -n 5
tail -f "$(ls -1t data/malicious_logs/*.jsonl | head -1)"
```

---

## Troubleshooting

**Agent loops “Connection refused”**
- Ensure `mosquitto.conf` has `listener 1883 0.0.0.0`
- Compose uses `depends_on: { mosquitto: { condition: service_healthy } }`
- In healthcheck, escape `$SYS` as `$$SYS`
- Verify agent env inside container:
  ```bash
  docker compose exec -T agent sh -lc 'echo "MQTT_HOST=$MQTT_HOST MQTT_PORT=$MQTT_PORT"'
  ```

**Empty files / no output**
- Generator not running or saver thresholds too strict  
- Run:
  ```bash
  ./manager.sh --overburst
  docker compose exec -T mosquitto sh -lc \
    "timeout 5s mosquitto_sub -h localhost -t 'sentinel/#' -v | head -20"
  ```

**Files owned by root**
```bash
sudo chown -R "$(id -u)":"$(id -g)" data
# persist with:
#   user: "${UID}:${GID}"
# and a .env (UID/GID) as above
```

**Compose v1 vs v2**
- Prefer `docker compose` (plugin).  
- If using `docker-compose` v1, remove `depends_on.condition` or upgrade.

**WSL**
- Ensure Docker Desktop WSL integration is enabled.

---

## Security & Privacy (MVP)

- MQTT is **unauthenticated** (dev only). For staging/prod:
  - `allow_anonymous false`, users/passwords or TLS
  - private network/VPN for broker
- `sample` is a salted hash; change `SALT` per deployment.

---

## Roadmap (post-v0.1)

- Per-method/ASN/region topics & policies  
- Durable queueing, backpressure, retries  
- Real-time dashboard (heatmap + drill-down)  
- Signed reports + on-chain attestations (karma oracle)  
- ML-based anomaly scores & adaptive thresholds

---

## Useful Snippets

**Validate JSON quickly**
```bash
jq -c . "$(ls -1t data/malicious_logs/*.jsonl | head -1)" >/dev/null && echo "JSON OK"
```

**Top methods in malicious logs**
```bash
cat data/malicious_logs/*.jsonl \
 | jq -r '.method // "unknown"' | sort | uniq -c | sort -nr | head -10
```

**Covered time range (by `ts`)**
```bash
cat data/malicious_logs/*.jsonl \
 | jq -s '[min_by(.ts).ts, max_by(.ts).ts] | @tsv' \
 | awk '{print "from:", strftime("%F %T", $1), "to:", strftime("%F %T", $2)}'
```

---

**You’re on v0.1 and the pipeline is healthy.**
If you want, I can add default thresholds + `user: "${UID}:${GID}"` to your compose so it’s clean out-of-the-box.
