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
  mkdir -p data data/logs_normal data/malicious_logs || true
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
  info "Installing base tools (jq, tmux, etc)…"
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg lsb-release jq tmux
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
  dc build agent generator saver
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
  ensure_dirs
  info "Ensuring services are up…"
  dc up -d mosquitto agent generator saver
  if command -v gnome-terminal >/dev/null 2>&1; then
    info "Opening GNOME Terminal dashboard"
    gnome-terminal \
      --window --title="SK: ps" -- bash -lc "cd '$ROOT'; watch -n1 $DCCMD ps; exec bash" \
      --tab --title="SK: MQTT sub" -- bash -lc "cd '$ROOT'; $DCCMD exec mosquitto mosquitto_sub -h localhost -t 'sentinel/#' -v; exec bash" \
      --tab --title="SK: mosquitto logs" -- bash -lc "cd '$ROOT'; $DCCMD logs -f mosquitto; exec bash" \
      --tab --title="SK: agent logs" -- bash -lc "cd '$ROOT'; $DCCMD logs -f agent; exec bash" \
      --tab --title="SK: generator logs" -- bash -lc "cd '$ROOT'; $DCCMD logs -f generator; exec bash" \
      --tab --title="SK: saver logs" -- bash -lc "cd '$ROOT'; $DCCMD logs -f saver; exec bash" \
      >/dev/null 2>&1 & disown || true
  else
    warn "gnome-terminal not found; using tmux"
    need_bin tmux || die "tmux not installed. Run: $0 --install"
    local S=skmon
    tmux kill-session -t "$S" 2>/dev/null || true
    tmux new-session -d -s "$S" -n mon "cd '$ROOT'; watch -n1 $DCCMD ps"
    tmux split-window -h -t "$S":0 "cd '$ROOT'; $DCCMD exec mosquitto mosquitto_sub -h localhost -t 'sentinel/#' -v"
    tmux split-window -v -t "$S":0.0 "cd '$ROOT'; $DCCMD logs -f mosquitto"
    tmux split-window -v -t "$S":0.2 "cd '$ROOT'; $DCCMD logs -f agent"
    tmux split-window -v -t "$S":0.3 "cd '$ROOT'; $DCCMD logs -f generator"
    tmux split-window -v -t "$S":0.4 "cd '$ROOT'; $DCCMD logs -f saver"
    tmux select-layout -t "$S":0 tiled
    tmux attach -t "$S"
  fi
}

do_stop(){ info "Stopping stack…"; dc down --remove-orphans || true; }

docker_purge_project(){
  info "Purging project containers/images…"
  dc down -v --remove-orphans || true
  docker image rm -f sentinelkarma-agent sentinelkarma-generator sentinelkarma-saver 2>/dev/null || true
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

do_overburst(){
  [[ -f docker-compose.yml ]] || die "Missing docker-compose.yml"
  [[ -n "$DCCMD" ]] || die "Compose not available. Run: $0 --docker"
  ensure_dirs
  info "Ensuring services are up (mosquitto+agent+generator+saver)…"
  dc up -d mosquitto agent generator saver

  info "OVERBURST: ${OVER_SECS}s per method @ rate=${OVER_RATE}, err=${OVER_ERR}, base_lat=${OVER_BASE_LAT}, burst_lat=${OVER_BURST_LAT}"
  for m in $OVER_METHODS; do
    info "Bursting method: $m"
    $DCCMD exec -T -d generator sh -lc \
      "python -m tools.generator --log /data/rpc.jsonl \
       --rate $OVER_RATE --burst '$m' \
       --err $OVER_ERR --baseline_lat $OVER_BASE_LAT --burst_lat $OVER_BURST_LAT \
       --burst_secs $OVER_SECS"
  done
  info "Overburst done. Check: data/malicious_logs/  (and data/logs_normal/)."
}

# ===================== CLI =====================
ACTION=""; VERBOSE=0
for a in "$@"; do
  case "$a" in
    --help)
      cat <<'HLP'
Usage: ./manager.sh [FLAGS]

  --help                  Show this help
  --check                 Show missing libraries/tools
  --install               Install base libs (ca-certificates, curl, gnupg, lsb-release, jq, tmux)
  --docker                Install Docker Engine + Compose v2, then build images (agent/generator/saver)
  --start [--verbose]     Start mosquitto; with --verbose tails its logs
  --test                  Up mosquitto+agent+generator+saver & start collectors (malicious/normal)
  --monitor               Dashboard: ps + MQTT sub + logs (mosquitto/agent/generator/saver)
  --overburst             Ruleaza un val “spicy” de trafic (vezi env OVER_*)
  --stop                  Stop all compose services
  --docker-purge          Remove project containers/images (no repo changes)
  --docker-reinstall      Purge Docker from system, reinstall, rebuild (asks confirm)

Env overrides:
  ERR_THR, ZLAT_THR, ZERR_THR, P95_THR, MAL_WINDOW_MIN (default 3), NOR_WINDOW_MIN (default 30)
  OVER_RATE, OVER_ERR, OVER_BASE_LAT, OVER_BURST_LAT, OVER_SECS, OVER_METHODS
HLP
      exit 0;;
    --check) ACTION="check" ;;
    --install) ACTION="install" ;;
    --docker) ACTION="docker" ;;
    --start) ACTION="start" ;;
    --verbose) VERBOSE=1 ;;
    --test) ACTION="test" ;;
    --monitor) ACTION="monitor" ;;
    --overburst) ACTION="overburst" ;;
    --stop) ACTION="stop" ;;
    --docker-purge) ACTION="docker-purge" ;;
    --docker-reinstall) ACTION="docker-reinstall" ;;
    *) die "Unknown flag: $a (use --help)" ;;
  esac
done

[[ -n "${ACTION:-}" ]] || { "$0" --help; exit 0; }

case "$ACTION" in
  check)            check_missing || exit 1 ;;
  install)          do_install_libs ;;
  docker)           docker_setup; build_images ;;
  start)            do_start "$VERBOSE" ;;
  test)             do_test ;;
  monitor)          do_monitor ;;
  overburst)        do_overburst ;;
  stop)             do_stop ;;
  docker-purge)     docker_purge_project ;;
  docker-reinstall) docker_reinstall ;;
  *) die "Unhandled action $ACTION" ;;
esac
