# agent-python/tools/saver.py
import asyncio, os, time
from urllib.parse import urlparse
import orjson
from aiomqtt import Client

class RotatingWriter:
    def __init__(self, base_dir: str, rotate_secs: int, namer=None):
        self.base_dir = base_dir
        self.rotate_secs = max(60, int(rotate_secs))  # minim 60s ca să nu abuzăm FS
        self.namer = namer  # optional function: (bin_start:int)->filename
        os.makedirs(base_dir, exist_ok=True)
        self._cur_bin = None
        self._fp = None

    def _path_for(self, bin_start: int) -> str:
        if callable(self.namer):
            return os.path.join(self.base_dir, self.namer(bin_start))
        t = time.gmtime(bin_start)  # UTC
        return os.path.join(
            self.base_dir,
            f"log-{t.tm_year:04d}{t.tm_mon:02d}{t.tm_mday:02d}-{t.tm_hour:02d}{t.tm_min:02d}.jsonl"
        )

    def write(self, obj: dict, ts: float):
        bin_start = int(ts // self.rotate_secs * self.rotate_secs)
        if bin_start != self._cur_bin:
            if self._fp:
                try:
                    self._fp.flush()
                finally:
                    self._fp.close()
            self._cur_bin = bin_start
            path = self._path_for(bin_start)
            # append + unbuffered (flushed on each write)
            self._fp = open(path, "ab", buffering=0)
        self._fp.write(orjson.dumps(obj) + b"\n")
        try:
            self._fp.flush()
        except Exception:
            pass

    def current_path(self) -> str | None:
        if self._cur_bin is None:
            return None
        return self._path_for(self._cur_bin)

    def close(self):
        if self._fp:
            try:
                self._fp.flush()
            finally:
                self._fp.close()
            self._fp = None

async def cleanup_loop(directory: str, ttl_secs: int, interval: int = 60, writer: RotatingWriter | None = None):
    """Șterge fișierele *.jsonl/*.log mai vechi decât ttl_secs, la fiecare `interval` secunde."""
    if ttl_secs <= 0:
        return
    os.makedirs(directory, exist_ok=True)
    while True:
        try:
            now = time.time()
            for name in os.listdir(directory):
                if not (name.endswith(".jsonl") or name.endswith(".log")):
                    continue
                path = os.path.join(directory, name)
                # nu ștergem fișierul în care scriem acum
                if writer and writer.current_path() == path:
                    continue
                try:
                    st = os.stat(path)
                    if now - st.st_mtime > ttl_secs:
                        os.remove(path)
                except FileNotFoundError:
                    pass
                except Exception:
                    # nu oprim bucla de curățare pentru un fișier problematic
                    pass
        except Exception:
            pass
        await asyncio.sleep(interval)

async def run():
    url = os.getenv("MQTT_URL", "mqtt://mosquitto:1883")

    normal_dir = os.getenv("NORMAL_DIR", "/data/logs_normal")
    malicious_dir = os.getenv("MALICIOUS_DIR", "/data/malicious_logs")

    # rotație separată
    normal_rotate_secs    = int(os.getenv("NORMAL_ROTATE_SECS", "1800"))  # 30 min
    malicious_rotate_secs = int(os.getenv("MALICIOUS_ROTATE_SECS", "180"))  # 3 min

    # retenție (TTL). 0 = păstrează la nesfârșit
    normal_ttl_mins       = int(os.getenv("NORMAL_TTL_MINS", "120"))  # 2 ore default
    malicious_ttl_mins    = int(os.getenv("MALICIOUS_TTL_MINS", "0"))  # default: nu ștergem

    z_thresh = float(os.getenv("Z_THRESHOLD", "3.0"))
    # Additional classification thresholds (fallback to Z_THRESHOLD for z.* if specific not provided)
    err_thr = float(os.getenv("ERR_THR", "0.05"))
    zlat_thr = float(os.getenv("ZLAT_THR", str(z_thresh)))
    zerr_thr = float(os.getenv("ZERR_THR", str(z_thresh)))
    p95_thr = float(os.getenv("P95_THR", "250"))

    os.makedirs(normal_dir, exist_ok=True)
    os.makedirs(malicious_dir, exist_ok=True)

    nw = RotatingWriter(normal_dir, normal_rotate_secs)
    # custom namer for malicious logs: "unixtimestamp_dd_mm_yy_h_m_s.log" (UTC)
    def mal_namer(bin_start: int) -> str:
        t = time.gmtime(bin_start)
        return f"{bin_start}_{t.tm_mday:02d}_{t.tm_mon:02d}_{t.tm_year % 100:02d}_{t.tm_hour:02d}_{t.tm_min:02d}_{t.tm_sec:02d}.log"

    mw = RotatingWriter(malicious_dir, malicious_rotate_secs, namer=mal_namer)

    u = urlparse(url)
    host = u.hostname or "localhost"
    port = u.port or 1883

    # pornesc curățarea în fundal (normal obligatoriu, malicious opțional)
    tasks = []
    tasks.append(asyncio.create_task(
        cleanup_loop(normal_dir, normal_ttl_mins * 60, 60, writer=nw)
    ))
    if malicious_ttl_mins > 0:
        tasks.append(asyncio.create_task(
            cleanup_loop(malicious_dir, malicious_ttl_mins * 60, 60, writer=mw)
        ))

    while True:
        try:
            async with Client(host, port) as client:
                await client.subscribe("sentinel/#")
                async with client.messages() as messages:
                    async for msg in messages:
                        topic = str(getattr(msg.topic, "value", msg.topic))
                        payload = msg.payload
                        try:
                            data = orjson.loads(payload)
                        except Exception:
                            data = {"raw": payload.decode("utf-8", "ignore")}
                        ts = data.get("ts")
                        if not isinstance(ts, (int, float)):
                            ts = time.time()

                        write_mal = topic.startswith("sentinel/alert")
                        z = data.get("z") or {}
                        metrics = data.get("metrics") or {}
                        if not write_mal:
                            try:
                                if float(z.get("lat", 0.0)) >= zlat_thr or float(z.get("err", 0.0)) >= zerr_thr:
                                    write_mal = True
                            except Exception:
                                pass
                        if not write_mal:
                            try:
                                if float(metrics.get("err_rate", 0.0)) >= err_thr or float(metrics.get("p95", 0.0)) >= p95_thr:
                                    write_mal = True
                            except Exception:
                                pass

                        if write_mal:
                            mw.write(data, ts)
                        else:
                            nw.write(data, ts)
        except Exception:
            # reconectare simplă MQTT
            await asyncio.sleep(1)

if __name__ == "__main__":
    import uvloop
    uvloop.install()
    asyncio.run(run())
