import asyncio
import os
import time
from urllib.parse import urlparse
import orjson
from aiomqtt import Client


class RotatingWriter:
    def __init__(self, base_dir: str, rotate_secs: int, namer=None):
        self.base_dir = base_dir
        self.rotate_secs = max(60, int(rotate_secs))
        self.namer = namer
        os.makedirs(base_dir, exist_ok=True)
        self._cur_bin = None
        self._fp = None

    def _path_for(self, bin_start: int) -> str:
        if callable(self.namer):
            return os.path.join(self.base_dir, self.namer(bin_start))
        t = time.gmtime(bin_start)
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
                if writer and writer.current_path() == path:
                    continue
                try:
                    st = os.stat(path)
                    if now - st.st_mtime > ttl_secs:
                        os.remove(path)
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
        except Exception:
            pass
        await asyncio.sleep(interval)


async def run():
    url = os.getenv("MQTT_URL", "mqtt://mosquitto:1883")
    normal_dir = os.getenv("NORMAL_DIR", "/data/logs_normal")
    malicious_dir = os.getenv("MALICIOUS_DIR", "/data/malicious_logs")
    normal_rotate_secs = int(os.getenv("NORMAL_ROTATE_SECS", "1800"))
    malicious_rotate_secs = int(os.getenv("MALICIOUS_ROTATE_SECS", "180"))
    normal_ttl_mins = int(os.getenv("NORMAL_TTL_MINS", "120"))
    malicious_ttl_mins = int(os.getenv("MALICIOUS_TTL_MINS", "0"))
    z_thresh = float(os.getenv("Z_THRESHOLD", "3.0"))
    err_thr = float(os.getenv("ERR_THR", "0.05"))
    zlat_thr = float(os.getenv("ZLAT_THR", str(z_thresh)))
    zerr_thr = float(os.getenv("ZERR_THR", str(z_thresh)))
    p95_thr = float(os.getenv("P95_THR", "250"))
    contract_dir = os.getenv("CONTRACT_DIR", "/data/contract_data")
    salt_id = int(os.getenv("SALT_ID", "0"))
    contract_max_attackers = int(os.getenv("CONTRACT_MAX_ATTACKERS", "10"))
    contract_ts_epoch = int(os.getenv("CONTRACT_TS_EPOCH", "1704067200"))

    os.makedirs(normal_dir, exist_ok=True)
    os.makedirs(malicious_dir, exist_ok=True)
    os.makedirs(contract_dir, exist_ok=True)

    nw = RotatingWriter(normal_dir, normal_rotate_secs)

    def mal_namer(bin_start: int) -> str:
        t = time.gmtime(bin_start)
        return f"{bin_start}_{t.tm_mday:02d}_{t.tm_mon:02d}_{t.tm_year % 100:02d}_{t.tm_hour:02d}_{t.tm_min:02d}_{t.tm_sec:02d}.log"

    mw = RotatingWriter(malicious_dir, malicious_rotate_secs, namer=mal_namer)

    current_cd_base = None
    current_cd_map: dict[str, int] = {}

    u = urlparse(url)
    host = u.hostname or "localhost"
    port = u.port or 1883

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
                            try:
                                pre_base = os.path.basename(mw.current_path()) if mw.current_path() else None
                            except Exception:
                                pre_base = None

                            counts = data.get("counts") if isinstance(data, dict) else None
                            ips = data.get("ips") if isinstance(data, dict) else None

                            current_record = None
                            if isinstance(counts, dict) or isinstance(ips, list):
                                region = data.get("region")
                                asn = data.get("asn")

                                total_calls = counts.get("calls") if isinstance(counts, dict) else None
                                if not isinstance(total_calls, (int, float)):
                                    total_calls = sum(int(x.get("requests", 0)) for x in (ips or [])) if ips else 0

                                unique_ips = counts.get("unique_iphash") if isinstance(counts, dict) else None
                                if not isinstance(unique_ips, (int, float)):
                                    unique_ips = len(ips or [])

                                errs = counts.get("errs") if isinstance(counts, dict) else None
                                if isinstance(errs, (int, float)) and total_calls > 0:
                                    avg_err_rate = float(errs) / float(total_calls)
                                else:
                                    avg_err_rate = float((data.get("metrics") or {}).get("err_rate", 0.0))

                                attackers = []
                                for x in (ips or []):
                                    iphash = str(x.get("iphash", ""))
                                    if iphash.startswith("iphash:"):
                                        iphash = iphash.split(":", 1)[1]
                                    attackers.append({
                                        "iphash": iphash,
                                        "requests": int(x.get("requests", 0)),
                                        "err_rate": float(x.get("err_rate", 0.0)),
                                    })
                                attackers.sort(key=lambda a: a["requests"], reverse=True)

                                summary = {
                                    "region": region,
                                    "asn": asn,
                                    "requests": int(total_calls) if total_calls is not None else 0,
                                    "unique_iphash": int(unique_ips) if unique_ips is not None else 0,
                                    "avg_err_rate": round(float(avg_err_rate), 4),
                                    "top_attackers": attackers,
                                }
                                mw.write(summary, ts)
                                current_record = summary
                            else:
                                mw.write(data, ts)
                                current_record = data

                            old_base = pre_base

                            iphashes = []
                            if isinstance(ips, list) and ips:
                                for x in ips:
                                    h = str(x.get("iphash", "")).lower()
                                    if h.startswith("iphash:"):
                                        h = h.split(":", 1)[1]
                                    h = "".join(c for c in h if c in "0123456789abcdef")
                                    if len(h) >= 12:
                                        iphashes.append(h[:12])
                            if not iphashes and isinstance(current_record, dict):
                                for x in (current_record.get("top_attackers") or []):
                                    h = str(x.get("iphash", "")).lower()
                                    if h.startswith("iphash:"):
                                        h = h.split(":", 1)[1]
                                    h = "".join(c for c in h if c in "0123456789abcdef")
                                    if len(h) >= 12:
                                        iphashes.append(h[:12])
                            if not iphashes and isinstance(current_record, dict):
                                h = (current_record.get("sample") or data.get("sample"))
                                if isinstance(h, str):
                                    h = h.lower()
                                    if h.startswith("iphash:"):
                                        h = h.split(":", 1)[1]
                                    h = "".join(c for c in h if c in "0123456789abcdef")
                                    if len(h) >= 12:
                                        iphashes.append(h[:12])

                            try:
                                new_base = os.path.basename(mw.current_path()) if mw.current_path() else None
                            except Exception:
                                new_base = None

                            rotated = old_base is not None and new_base is not None and old_base != new_base

                            if rotated and current_cd_base and current_cd_base == old_base:
                                try:
                                    bin_str = old_base.split("_", 1)[0]
                                    bin_start = int(bin_str)
                                except Exception:
                                    bin_start = int(ts // malicious_rotate_secs * malicious_rotate_secs)

                                ts32 = bin_start - contract_ts_epoch
                                if ts32 < 0:
                                    ts32 = 0
                                items = sorted(current_cd_map.items(), key=lambda kv: (-kv[1], kv[0]))
                                entries = [k for k, _ in items][:max(0, contract_max_attackers)]
                                contract_obj = {
                                    "v": 1,
                                    "sid": int(salt_id),
                                    "t": int(ts32),
                                    "cnt": len(entries),
                                    "cap": int(contract_max_attackers),
                                    "ent": [{"iph6": h} for h in entries],
                                }
                                out_path = os.path.join(contract_dir, f"cd_{old_base}")
                                try:
                                    with open(out_path, "wb") as scf:
                                        scf.write(orjson.dumps(contract_obj))
                                        scf.write(b"\n")
                                except Exception:
                                    pass
                                current_cd_map.clear()
                                current_cd_base = None

                            if new_base:
                                if current_cd_base is None:
                                    current_cd_base = new_base
                                elif current_cd_base != new_base:
                                    current_cd_map.clear()
                                    current_cd_base = new_base

                                for h in iphashes:
                                    if not h:
                                        continue
                                    current_cd_map[h] = current_cd_map.get(h, 0) + 1

                        else:
                            nw.write(data, ts)
        except Exception:
            await asyncio.sleep(1)


if __name__ == "__main__":
    import uvloop
    uvloop.install()
    asyncio.run(run())
