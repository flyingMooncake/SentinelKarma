#!/usr/bin/env bash
set -euo pipefail

# SentinelKarma manager
# - NU creeaza/editeaza fisiere din repo (doar ruleaza procese/docker)
# - colectori split: data/malicious_logs (3m), data/logs_normal (30m)
# - tmux fallback daca nu exista gnome-terminal

# ===================== Config & praguri =====================
ERR_THR="${ERR_THR:-0.05}"        # err_rate >= 5% => malicious
ZLAT_THR="${ZLAT_THR:-4}"         # z.lat   >= 4σ  => malicious
ZERR_THR="${ZERR_THR:-2}"         # z.err   >= 2σ  => malicious
P95_THR="${P95_THR:-250}"         # p95(ms) >= 250 => malicious
MAL_WINDOW_MIN="${MAL_WINDOW_MIN:-3}"     # rotatie 3 minute (malicious)
NOR_WINDOW_MIN="${NOR_WINDOW_MIN:-30}"    # rotatie 30 minute (normal)

# Overburst defaults (override cu env)
OVER_RATE="${OVER_RATE:-2000}"
OVER_ERR="${OVER_ERR:-0.7}"
OVER_BASE_LAT="${OVER_BASE_LAT:-220}"
OVER_BURST_LAT="${OVER_BURST_LAT:-480}"
OVER_SECS="${OVER_SECS:-90}"
OVER_METHODS="${OVER_METHODS:-getProgramAccounts getLogs}"
OVER_PARALLEL="${OVER_PARALLEL:-1}"

info(){ printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn(){ printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err(){  printf "\033[1;31m[ERR ]\033[0m %s\n" "$*" >&2; }
die(){  err "$*"; exit 1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

HAS_SUDO=1; command -v sudo >/dev/null 2>&1 || HAS_SUDO=0
need_sudo(){ [[ $HAS_SUDO -eq 1 ]] || die "sudo required"; sudo -v; }

# ===================== Compose detection =====================
DCCMD=""
if docker compose version >/dev/null 2>&1; then
  DCCMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DCCMD="docker-compose"
fi
dc(){
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    die "Compose not available. Run: $0 --docker"
  fi
}

# ===================== Helpers =====================
need_pkg(){ dpkg -s "$1" >/dev/null 2>&1; }
need_bin(){ command -v "$1" >/dev/null 2>&1; }

ensure_dirs(){
  mkdir -p data data/logs_normal data/malicious_logs data/logs || true
  chmod 777 data || true
}

check_missing(){
  local missing=()
  need_bin curl || missing+=(curl)
  need_bin gpg || missing+=(gnupg)
  need_pkg ca-certificates || missing+=(ca-certificates)
  need_pkg lsb-release || missing+=(lsb-release)
  need_bin docker || missing+=(docker)
  [[ -n "$DCCMD" ]] || missing+=(docker-compose-plugin)
  need_bin jq || missing+=(jq)
  need_bin tmux || missing+=(tmux)
  need_bin watch || missing+=(procps)
  if [[ ! -f docker-compose.yml ]]; then
    warn "docker-compose.yml lipseste in $ROOT (managerul NU modifica repo-ul)."
  fi
  if ((${#missing[@]})); then
    echo "Missing: ${missing[*]}"; return 1
  else
    echo "All required tools present."; return 0
  fi
}

do_install_libs(){
  need_sudo
  info "Installing base tools (jq, tmux, nodejs, etc)…"
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg lsb-release jq tmux procps wget git
  
  # Install Node.js 20.x if not present or outdated
  if ! command -v node >/dev/null 2>&1 || [[ $(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1) -lt 18 ]]; then
    info "Installing Node.js 20.x…"
    
    # Remove conflicting old Node.js packages first
    info "Removing old Node.js packages if present…"
    sudo apt-get remove -y libnode-dev node-gyp libnode72 nodejs-doc 2>/dev/null || true
    sudo apt-get remove -y nodejs npm 2>/dev/null || true
    sudo apt-get autoremove -y 2>/dev/null || true
    
    # Clean apt cache to avoid conflicts
    sudo apt-get clean
    sudo rm -rf /var/cache/apt/archives/nodejs*.deb 2>/dev/null || true
    
    # Setup NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    
    # Force install with overwrite if needed
    sudo apt-get install -y nodejs || sudo dpkg -i --force-overwrite /var/cache/apt/archives/nodejs*.deb && sudo apt-get install -f -y
  else
    info "Node.js $(node --version) already installed"
  fi
  
  # Verify npm is available (comes with nodejs from NodeSource)
  if ! command -v npm >/dev/null 2>&1; then
    warn "npm not found, but should be included with Node.js"
  fi
  
  info "Done."
}

docker_setup(){
  need_sudo
  if ! need_bin docker; then
    info "Adding Docker APT repo…"
    sudo install -m 0755 -d /etc/apt/keyrings
    [[ -f /etc/apt/keyrings/docker.gpg ]] || \
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    local codename="$(. /etc/os-release && echo "$VERSION_CODENAME")"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${codename} stable" \
      | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    sudo apt-get update -y
    info "Installing Docker Engine + Compose v2…"
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  else
    info "Docker present: $(docker --version)"
    if [[ -z "$DCCMD" ]]; then
      sudo apt-get update -y
      sudo apt-get install -y docker-compose-plugin || true
    fi
  fi
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl enable --now docker || true
  else
    sudo service docker start || true
  fi
  if ! id -nG "$USER" | grep -qE '(^| )docker( |$)'; then
    info "Adding $USER to docker group…"; sudo usermod -aG docker "$USER" || true
    warn "Deschide un shell NOU ca sa se aplice group= docker."
  fi
  # refresh DCCMD
  if docker compose version >/dev/null 2>&1; then
    DCCMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    DCCMD="docker-compose"
  fi
  [[ -f docker-compose.yml ]] || warn "No docker-compose.yml in repo."
}

build_images(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  info "Building images…"
  dc build agent generator saver log-server web
}

do_start(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  [[ -n "$DCCMD" ]] || die "Compose not available. Run: $0 --docker"
  local verbose="${1:-0}"
  ensure_dirs
  info "Starting mosquitto…"
  dc up -d mosquitto
  [[ "$verbose" == "1" ]] && dc logs -f mosquitto || true
}

# ===================== Collectors (no repo changes) =====================
collector_mal_cmd(){
  cat <<'EOF'
set -euo pipefail
echo "[collector-mal] thresholds: ERR_THR=$ERR_THR ZLAT_THR=$ZLAT_THR ZERR_THR=$ZERR_THR P95_THR=$P95_THR; window=${MAL_WINDOW_MIN}m"
while :; do
  ts="$(date +%Y%m%d_%H%M%S)"
  out="data/malicious_logs/${ts}.jsonl"
  echo "[collector-mal] writing -> $out"
  timeout "${MAL_WINDOW_MIN}m" bash -lc "$DCCMD exec -T mosquitto mosquitto_sub -h localhost -t 'sentinel/#' -v" \
    | cut -d' ' -f2- \
    | jq -c --argjson et "$ERR_THR" --argjson zl "$ZLAT_THR" --argjson ze "$ZERR_THR" --argjson p "$P95_THR" \
        'select((.metrics.err_rate // 0) >= $et or (.z.lat // 0) >= $zl or (.z.err // 0) >= $ze or (.metrics.p95 // 0) >= $p)' \
    | stdbuf -oL tee -a "$out" >/dev/null
done
EOF
}

collector_norm_cmd(){
  cat <<'EOF'
set -euo pipefail
echo "[collector-norm] thresholds: ERR_THR=$ERR_THR ZLAT_THR=$ZLAT_THR ZERR_THR=$ZERR_THR P95_THR=$P95_THR; window=${NOR_WINDOW_MIN}m"
while :; do
  ts="$(date +%Y%m%d_%H%M)"
  out="data/logs_normal/${ts}.jsonl"
  echo "[collector-norm] writing -> $out"
  timeout "${NOR_WINDOW_MIN}m" bash -lc "$DCCMD exec -T mosquitto mosquitto_sub -h localhost -t 'sentinel/#' -v" \
    | cut -d' ' -f2- \
    | jq -c --argjson et "$ERR_THR" --argjson zl "$ZLAT_THR" --argjson ze "$ZERR_THR" --argjson p "$P95_THR" \
        'select((.metrics.err_rate // 0) < $et and (.z.lat // 0) < $zl and (.z.err // 0) < $ze and (.metrics.p95 // 0) < $p)' \
    | stdbuf -oL tee -a "$out" >/dev/null
done
EOF
}

do_test(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  [[ -n "$DCCMD" ]] || die "Compose not available. Run: $0 --docker"
  ensure_dirs
  info "Starting mosquitto + agent + generator + saver…"
  dc up -d mosquitto agent generator saver

  # export pentru subshell-urile colectorilor
  export ERR_THR ZLAT_THR ZERR_THR P95_THR MAL_WINDOW_MIN NOR_WINDOW_MIN DCCMD ROOT

  if command -v gnome-terminal >/dev/null 2>&1; then
    info "Opening GNOME terminals: MQTT sub + generator + collectors"
    gnome-terminal \
      --window --title="SK MQTT sub" -- bash -lc "cd '$ROOT'; $DCCMD exec mosquitto mosquitto_sub -h localhost -t 'sentinel/#' -v; exec bash" \
      --tab --title="SK Generator" -- bash -lc "cd '$ROOT'; $DCCMD exec generator python -m tools.generator --log /data/rpc.jsonl --rate 1000 --burst getProgramAccounts --err 0.2 --burst_secs 2; exec bash" \
      --tab --title="SK Collector MAL" -- bash -lc "cd '$ROOT'; $(collector_mal_cmd); exec bash" \
      --tab --title="SK Collector NORM" -- bash -lc "cd '$ROOT'; $(collector_norm_cmd); exec bash" \
      >/dev/null 2>&1 & disown || true
  else
    warn "gnome-terminal not found; using tmux"
    need_bin tmux || die "tmux not installed. Run: $0 --install"
    local S=sktest
    tmux kill-session -t "$S" 2>/dev/null || true
    tmux new-session -d -s "$S" -n test "cd '$ROOT'; $DCCMD exec mosquitto mosquitto_sub -h localhost -t 'sentinel/#' -v"
    tmux split-window -h -t "$S":0 "cd '$ROOT'; $DCCMD exec generator python -m tools.generator --log /data/rpc.jsonl --rate 1000 --burst getProgramAccounts --err 0.2 --burst_secs 2"
    tmux split-window -v -t "$S":0.0 "cd '$ROOT'; $(collector_mal_cmd)"
    tmux split-window -v -t "$S":0.2 "cd '$ROOT'; $(collector_norm_cmd)"
    tmux select-layout -t "$S":0 tiled
    tmux select-pane -t "$S":0.1
    tmux attach -t "$S"
  fi
}

do_monitor(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  [[ -n "$DCCMD" ]] || die "Compose not available. Run: $0 --docker"
  info "Ensuring services are up…"
  if [[ "${MON_ALL:-0}" -eq 1 ]]; then
    dc up -d mosquitto agent saver generator log-server
  else
    dc up -d mosquitto agent saver log-server
  fi
  
  # Wait for log-server to be healthy
  info "Waiting for log-server to be ready…"
  for i in {1..30}; do
    if curl -sf http://localhost:9000/health >/dev/null 2>&1; then
      info "Log server is ready at http://localhost:9000"
      break
    fi
    [[ $i -eq 30 ]] && warn "Log server health check timeout (may still be starting)"
    sleep 1
  done
  
  # If --full flag, start auto-mint monitor
  if [[ "${FULL_MONITOR:-0}" -eq 1 ]]; then
    info "Starting FULL monitoring mode (auto-mint + upload)..."
    info "This will automatically process new contract data files"
    
    if [[ ! -f "scripts/auto_mint_monitor.py" ]]; then
      err "Auto-mint monitor script not found!"
      return 1
    fi
    
    chmod +x scripts/auto_mint_monitor.py 2>/dev/null || true
    python3 scripts/auto_mint_monitor.py
    return 0
  fi
  
  if [[ "${MUTE:-0}" -eq 1 ]]; then
    info "Monitor started in background. Structured feed available via: $DCCMD exec -T agent python -m tools.monitor"
    info "Log server running at http://localhost:9000 (health: http://localhost:9000/health)"
    return 0
  fi
  local vflag="0"
  [[ "${VERBOSE:-0}" -eq 1 ]] && vflag="1"
  info "Streaming structured MQTT feed (attacks-only by default; use --verbose for all)…"
  info "Log server running at http://localhost:9000"
  MONITOR_VERBOSE="$vflag" $DCCMD exec -T agent python -m tools.monitor
}

do_web(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  [[ -n "$DCCMD" ]] || die "Compose not available. Run: $0 --docker"
  
  info "Starting web dashboard and dependencies…"
  ensure_dirs
  
  # Start required services
  dc up -d mosquitto log-server web
  
  # If --monitor-all, also start generator
  if [[ "${MON_ALL:-0}" -eq 1 ]]; then
    info "Starting generator for demo data…"
    dc up -d generator
  fi
  
  # Wait for web to be ready
  info "Waiting for web dashboard to be ready…"
  for i in {1..30}; do
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
      info "✓ Web dashboard is ready!"
      info "╔════════════════════════════════════════════════════════════╗"
      info "║  SentinelKarma Security Dashboard                         ║"
      info "║  Access at: http://localhost:3000                         ║"
      info "║  API Server: http://localhost:9000                        ║"
      info "╚════════════════════════════════════════════════════════════╝"
      
      # Open browser if available
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:3000 2>/dev/null &
      elif command -v open >/dev/null 2>&1; then
        open http://localhost:3000 2>/dev/null &
      fi
      
      break
    fi
    [[ $i -eq 30 ]] && warn "Web dashboard health check timeout (may still be starting)"
    sleep 1
  done
  
  if [[ "${MUTE:-0}" -ne 1 ]]; then
    info "Press Ctrl+C to stop"
    dc logs -f web
  fi
}

do_update(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  [[ -n "$DCCMD" ]] || die "Compose not available. Run: $0 --docker"
  
  info "Updating application components…"
  
  # Pull latest changes if in git repo
  if [[ -d .git ]]; then
    info "Pulling latest changes from git…"
    git pull || warn "Git pull failed, continuing with local version"
  fi
  
  # Update Node dependencies for web app
  if [[ -f app/package.json ]]; then
    info "Updating web app dependencies…"
    (cd app && npm install) || warn "npm install failed"
  fi
  
  # Rebuild all images
  info "Rebuilding Docker images…"
  dc build --no-cache agent generator saver log-server web
  
  # Restart services
  info "Restarting services with new images…"
  dc down
  dc up -d
  
  info "✓ Update complete!"
  info "Services have been restarted with the latest version."
}

do_stop(){ info "Stopping stack…"; dc down --remove-orphans || true; }

docker_purge_project(){
  info "Purging project containers/images…"
  dc down -v --remove-orphans || true
  docker image rm -f sentinelkarma-agent sentinelkarma-generator sentinelkarma-saver sentinelkarma-log-server sentinelkarma-web 2>/dev/null || true
  docker image prune -f >/dev/null || true
  docker builder prune -f >/dev/null || true
  info "Done."
}

docker_reinstall(){
  need_sudo
  docker_purge_project
  read -r -p "This will REMOVE Docker packages & data. Continue? [y/N] " a || true
  [[ "${a,,}" =~ ^y(es)?$ ]] || { info "Aborted."; exit 1; }
  (sudo systemctl stop docker 2>/dev/null || sudo service docker stop 2>/dev/null || true)
  sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || true
  sudo apt-get autoremove -y --purge || true
  sudo rm -rf /var/lib/docker /var/lib/containerd || true
  sudo rm -f /etc/apt/sources.list.d/docker.list /etc/apt/keyrings/docker.gpg || true
  docker_setup
  build_images
  info "Reinstall complete."
}

do_solana(){
  # Check if submodule exists
  if [[ ! -d "solanaTestNetDocker" ]]; then
    err "Solana testnet submodule not found!"
    info "Initialize it with: git submodule update --init --recursive"
    exit 1
  fi
  
  cd solanaTestNetDocker || die "Cannot enter solanaTestNetDocker directory"
  
  # Handle stop command
  if [[ "${SOLANA_STOP:-0}" -eq 1 ]]; then
    info "Stopping Solana testnet..."
    if [[ -f manager.sh ]]; then
      ./manager.sh --stop
    else
      docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
    fi
    cd "$ROOT"
    info "Solana testnet stopped"
    return 0
  fi
  
  # Check if manager.sh exists in submodule
  if [[ ! -f manager.sh ]]; then
    err "manager.sh not found in solanaTestNetDocker!"
    info "Make sure the submodule is properly initialized"
    cd "$ROOT"
    exit 1
  fi
  
  # Make manager.sh executable
  chmod +x manager.sh 2>/dev/null || true
  
  # Initialize if needed
  if [[ ! -d "data" ]] || [[ ! -f "data/config/validator-keypair.json" ]]; then
    info "Initializing Solana testnet for first time..."
    ./manager.sh --init || die "Failed to initialize Solana testnet"
  fi
  
  # Start validator
  if [[ "${SILENT:-0}" -eq 1 ]]; then
    info "Starting Solana testnet in background..."
    ./manager.sh --validate --silent
  else
    info "Starting Solana testnet..."
    ./manager.sh --validate
  fi
  
  cd "$ROOT"
  
  # Wait for validator to be ready
  info "Waiting for Solana validator to be ready..."
  for i in {1..30}; do
    if curl -sf http://localhost:8899 -X POST -H "Content-Type: application/json" \
         -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' >/dev/null 2>&1; then
      info "✓ Solana testnet is ready!"
      info "RPC URL: http://localhost:8899"
      info "WebSocket: ws://localhost:8900"
      break
    fi
    [[ $i -eq 30 ]] && warn "Solana health check timeout (may still be starting)"
    sleep 2
  done
}

do_overburst(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  [[ -n "$DCCMD" ]] || die "Compose not available. Run: $0 --docker"
  ensure_dirs
  info "Ensuring services are up (mosquitto+agent+generator+saver)…"
  dc up -d mosquitto agent generator saver

  # quick sanity check that generator has the module
  if ! $DCCMD exec -T generator python -c "import tools.generator" >/dev/null 2>&1; then
    die "generator container missing tools.generator module"
  fi

  # normalize method list and compute collection window
  local methods_norm
  methods_norm="${OVER_METHODS//,/ }"
  local mcount=0
  if [[ -n "${methods_norm// }" ]]; then
    # shellcheck disable=SC2046
    set -- $methods_norm
    mcount=$#
  fi
  local collect_secs
  if [[ "${OVER_PARALLEL}" -eq 1 ]]; then
    collect_secs=$(( OVER_SECS + 15 ))
  else
    collect_secs=$(( mcount * OVER_SECS + 15 ))
  fi

  # start a temporary malicious collector for the duration
  local ts out
  ts="$(date +%Y%m%d_%H%M%S)"
  out="data/malicious_logs/overburst_${ts}.jsonl"
  info "Collecting malicious diagnostics for ~${collect_secs}s -> $out"
  touch "$out" || true
  (
    timeout "${collect_secs}s" bash -lc "$DCCMD exec -T mosquitto mosquitto_sub -h localhost -t 'sentinel/#' -v" \
      | cut -d' ' -f2- \
      | jq -c --argjson et "$ERR_THR" --argjson zl "$ZLAT_THR" --argjson ze "$ZERR_THR" --argjson p "$P95_THR" \
          'select((.metrics.err_rate // 0) >= $et or (.z.lat // 0) >= $zl or (.z.err // 0) >= $ze or (.metrics.p95 // 0) >= $p)' \
      | stdbuf -oL tee -a "$out" >/dev/null
  ) & COLLECT_PID=$!

  info "OVERBURST: ${OVER_SECS}s per method @ rate=${OVER_RATE}, err=${OVER_ERR}, base_lat=${OVER_BASE_LAT}, burst_lat=${OVER_BURST_LAT}; parallel=${OVER_PARALLEL}"
  for m in $methods_norm; do
    info "Bursting method: $m"
    if [[ "${OVER_PARALLEL}" -eq 1 ]]; then
      # Background inside the container for broad compatibility (no -d needed)
      $DCCMD exec -T generator sh -lc \
        "nohup python -m tools.generator --log /data/rpc.jsonl \
         --rate $OVER_RATE --burst '$m' \
         --err $OVER_ERR --baseline_lat $OVER_BASE_LAT --burst_lat $OVER_BURST_LAT \
         --burst_secs $OVER_SECS > /tmp/overburst_${m}.log 2>&1 &"
    else
      # Sequential: wait for each burst to complete
      $DCCMD exec -T generator sh -lc \
        "python -m tools.generator --log /data/rpc.jsonl \
         --rate $OVER_RATE --burst '$m' \
         --err $OVER_ERR --baseline_lat $OVER_BASE_LAT --burst_lat $OVER_BURST_LAT \
         --burst_secs $OVER_SECS"
    fi
  done

  if [[ "${OVER_PARALLEL}" -eq 1 ]]; then
    info "Overburst launched in background. Collector will stop automatically in ~${collect_secs}s. Tail: docker compose logs -f generator; output file: $out"
  else
    info "Waiting for collector to finish (~${collect_secs}s total)…"
    wait $COLLECT_PID || true
    info "Overburst completed. Check: $out (and data/logs_normal/ if applicable)."
  fi
}

# ===================== CLI =====================
ACTION=""; VERBOSE=0; MON_ALL=0; MUTE=0; SILENT=0; SOLANA_STOP=0; FULL_MONITOR=0
for a in "$@"; do
  case "$a" in
    --help)
      cat <<'HLP'
Usage: ./manager.sh [FLAGS]

  --help                  Show this help
  --check                 Show missing libraries/tools
  --install               Install base libs (ca-certificates, curl, gnupg, lsb-release, jq, tmux)
  --docker                Install Docker Engine + Compose v2, then build images (agent/generator/saver/log-server)
  --start [--verbose]     Start mosquitto; with --verbose tails its logs
  --test                  Up mosquitto+agent+generator+saver & start collectors (malicious/normal)
  --monitor               Structured MQTT feed (attacks only) + log-server. Add --verbose for all telemetry; --monitor-all to also start generator
  --full                  Enable FULL monitoring mode (auto-mint + upload new contract data)
  --mute                  Detach monitor (run in background; view feed: docker compose exec -T agent python -m tools.monitor)
  --overburst             Ruleaza un val “spicy” de trafic (vezi env OVER_*)
  --stop                  Stop all compose services
  --docker-purge          Remove project containers/images (no repo changes)
  --docker-reinstall      Purge Docker from system, reinstall, rebuild (asks confirm)
  --solana [--silent]     Start Solana test validator (uses solanaTestNetDocker submodule)
  --solana --stop         Stop Solana test validator
  --local_network         [deprecated] Alias for --solana

Env overrides:
  ERR_THR, ZLAT_THR, ZERR_THR, P95_THR, MAL_WINDOW_MIN (default 3), NOR_WINDOW_MIN (default 30)
  OVER_RATE, OVER_ERR, OVER_BASE_LAT, OVER_BURST_LAT, OVER_SECS, OVER_METHODS (space or comma-separated), OVER_PARALLEL (1 parallel, 0 sequential)
HLP
      exit 0;;
    --check) ACTION="check" ;;
    --install) ACTION="install" ;;
    --docker) ACTION="docker" ;;
    --start) ACTION="start" ;;
    --verbose) VERBOSE=1 ;;
    --silent) SILENT=1 ;;
    --test) ACTION="test" ;;
    --web) ACTION="web" ;;
    --update) ACTION="update" ;;
    --solana) ACTION="solana" ;;
    --monitor) ACTION="monitor" ;;
    --monitor-all) MON_ALL=1 ;;
    --full) FULL_MONITOR=1 ;;
    --mute) MUTE=1 ;;
    --overburst) ACTION="overburst" ;;
    --stop)
      if [[ "$ACTION" == "solana" ]]; then
        SOLANA_STOP=1
      else
        ACTION="stop"
      fi
      ;;
    --docker-purge) ACTION="docker-purge" ;;
    --docker-reinstall) ACTION="docker-reinstall" ;;
    --local_network) ACTION="solana" ;;
    *) die "Unknown flag: $a (use --help)" ;;
  esac
done

[[ -n "${ACTION:-}" ]] || { "$0" --help; exit 0; }

case "$ACTION" in
  check)            check_missing || exit 1 ;;
  install)          do_install_libs ;;
  docker)           docker_setup; build_images ;;
  update)           do_update ;;
  start)            do_start "$VERBOSE" ;;
  test)             do_test ;;
  web)              do_web ;;
  monitor)          do_monitor ;;
  overburst)        do_overburst ;;
  stop)             do_stop ;;
  docker-purge)     docker_purge_project ;;
  docker-reinstall) docker_reinstall ;;
  solana)          do_solana ;;
  local_network)   do_solana ;;
  *) die "Unhandled action $ACTION" ;;
esac
