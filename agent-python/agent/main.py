import os, asyncio, time, hashlib, json, sys
import uvloop
import orjson
from urllib.parse import urlparse
from tdigest import TDigest
import aiomqtt

# ===================== Config din ENV =====================
MQTT_URL    = os.getenv("MQTT_URL", "mqtt://mosquitto:1883")
LOG_PATH    = os.getenv("LOG_PATH", "/data/rpc.jsonl")
REGION      = os.getenv("REGION", "eu-central")
ASN         = int(os.getenv("ASN", "64512"))
WINDOW_MS   = int(os.getenv("WINDOW_MS", "250"))
Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "3.0"))
SALT        = os.getenv("SALT", "change-me")  # pt. hash IP (no PII)
METHODS_HEAVY = set(os.getenv("METHODS_HEAVY", "getProgramAccounts,getLogs").split(","))

# ==== Parse MQTT_URL -> host/port (fix pentru aiomqtt.Client) ====
def parse_mqtt(url: str):
    u = urlparse(url)
    if u.scheme in ("mqtt", "tcp", ""):
        return (u.hostname or url, u.port or 1883, False)
    if u.scheme in ("mqtts", "ssl", "tls"):
        return (u.hostname or url, u.port or 8883, True)
    # dacă vine doar un hostname fără schemă
    if "://" not in url:
        return (url, 1883, False)
    raise ValueError(f"Unsupported MQTT_URL: {url}")

MQTT_HOST, MQTT_PORT, MQTT_TLS = parse_mqtt(MQTT_URL)

# ===================== Utilitare =====================
def ip_hash(ip: str, salt: str) -> str:
    h = hashlib.blake2b((ip + "|" + salt).encode(), digest_size=6)
    return "iphash:" + h.hexdigest()

class EWMA:
    def __init__(self, alpha=0.2):
        self.mu = None; self.var = 1e-6; self.a = alpha
    def update(self, x: float):
        if self.mu is None: self.mu = x; return
        d = x - self.mu
        self.mu += self.a * d
        self.var = (1 - self.a) * (self.var + self.a * d * d)
    def z(self, x: float) -> float:
        if self.mu is None: return 0.0
        return (x - self.mu) / ((self.var + 1e-9) ** 0.5)

class WindowStats:
    def __init__(self):
        self.tdigest = TDigest()
        self.calls = 0
        self.errs = 0
        self.lat_ewma = EWMA(0.15)
        self.err_ewma = EWMA(0.10)
    def add(self, latency_ms: float, is_err: bool):
        self.calls += 1
        self.tdigest.update(latency_ms)
        self.lat_ewma.update(latency_ms)
        if is_err:
            self.errs += 1
            self.err_ewma.update(1.0)
        else:
            self.err_ewma.update(0.0)
    def snapshot(self):
        p95 = float(self.tdigest.percentile(95.0)) if self.calls else 0.0
        err_rate = self.errs / max(1, self.calls)
        z_lat = self.lat_ewma.z(p95)
        z_err = self.err_ewma.z(err_rate)
        return p95, err_rate, z_lat, z_err

async def tail_log(path: str):
    """Tail simplu de fișier JSONL; re-deschide dacă e rotit sau lipsește."""
    pos = 0
    while True:
        try:
            with open(path, "rb") as f:
                if pos == 0:
                    f.seek(0, 2)  # start la EOF
                else:
                    try:
                        f.seek(pos)
                    except Exception:
                        f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.02)
                        pos = f.tell()
                        break
                    yield line
        except FileNotFoundError:
            await asyncio.sleep(0.25)

async def heartbeat_task(pub):
    """Trimite telemetrie ușoară o dată la 5s, să vezi trafic mereu."""
    while True:
        try:
            msg = orjson.dumps({
                "ts": int(time.time()),
                "region": REGION,
                "asn": ASN,
                "status": "ok"
            })
            await pub("sentinel/health", msg)
        except Exception as e:
            print(f"[heartbeat] publish failed: {e}", file=sys.stderr)
        await asyncio.sleep(5)

async def run_agent():
    print(f"[agent] starting. MQTT={MQTT_HOST}:{MQTT_PORT} TLS={MQTT_TLS} LOG_PATH={LOG_PATH}")
    windows = {}
    last_flush = time.time()

    while True:
        try:
            # conectare cu retry
            print("[agent] connecting MQTT...")
            async with aiomqtt.Client(hostname=MQTT_HOST, port=MQTT_PORT) as mq:
                print("[agent] MQTT connected.")
                async def pub(topic, payload):
                    await mq.publish(topic, payload, qos=0)

                # pornesc heartbeat
                hb = asyncio.create_task(heartbeat_task(pub))

                # loop principal: tail log + alerte
                async for raw in tail_log(LOG_PATH):
                    try:
                        ev = orjson.loads(raw)
                    except Exception:
                        try:
                            ev = json.loads(raw.decode("utf-8","ignore"))
                        except Exception:
                            continue

                    method = ev.get("method")
                    if method not in METHODS_HEAVY:
                        continue

                    ip = ev.get("ip", "0.0.0.0")
                    lat = float(ev.get("lat_ms", 0))
                    status = int(ev.get("status", 200))
                    is_err = status >= 500

                    w = windows.get(method)
                    if w is None:
                        w = windows[method] = WindowStats()
                    w.add(lat, is_err)

                    now = time.time()
                    if (now - last_flush) * 1000 >= WINDOW_MS:
                        ts = int(now)
                        for m, ws in list(windows.items()):
                            p95, err_rate, z_lat, z_err = ws.snapshot()
                            if z_lat >= Z_THRESHOLD or z_err >= Z_THRESHOLD:
                                msg = {
                                    "ts": ts,
                                    "window_ms": WINDOW_MS,
                                    "region": REGION,
                                    "asn": ASN,
                                    "method": m,
                                    "metrics": {
                                        "p95": round(p95,2),
                                        "err_rate": round(err_rate,4),
                                    },
                                    "z": {"lat": round(z_lat,2), "err": round(z_err,2)},
                                    "sample": ev.get("ip") and ip_hash(ip, SALT)
                                }
                                await pub("sentinel/diag", orjson.dumps(msg))
                        windows.clear()
                        last_flush = now

                hb.cancel()
        except Exception as e:
            # de ex: brokerul nu e gata încă
            print(f"[agent] MQTT loop error: {e}. reconnect in 1s...", file=sys.stderr)
            await asyncio.sleep(1)

if __name__ == "__main__":
    uvloop.install()
    asyncio.run(run_agent())
