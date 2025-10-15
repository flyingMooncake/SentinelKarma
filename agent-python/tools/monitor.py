import asyncio
import os
import json
import time
from urllib.parse import urlparse
import orjson
from aiomqtt import Client

RED = "\033[1;31m"
GREEN = "\033[1;32m"
CYAN = "\033[36m"
DIM = "\033[2m"
RESET = "\033[0m"

COLOR = os.getenv("MONITOR_COLOR", "1").lower() in ("1", "true", "yes", "on")
VERBOSE = os.getenv("MONITOR_VERBOSE", "0").lower() in ("1", "true", "yes", "on")
Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "3.0"))
ERR_THR = float(os.getenv("ERR_THR", "0.05"))
P95_THR = float(os.getenv("P95_THR", "250"))
ZLAT_THR = float(os.getenv("ZLAT_THR", str(Z_THRESHOLD)))
ZERR_THR = float(os.getenv("ZERR_THR", str(Z_THRESHOLD)))
MQTT_URL = os.getenv("MQTT_URL", "mqtt://mosquitto:1883")


def classify(topic: str, data: dict) -> bool:
    if topic.startswith("sentinel/alert"):
        return True
    z = data.get("z") or {}
    metrics = data.get("metrics") or {}
    try:
        if float(z.get("lat", 0.0)) >= ZLAT_THR or float(z.get("err", 0.0)) >= ZERR_THR:
            return True
    except Exception:
        pass
    try:
        if float(metrics.get("err_rate", 0.0)) >= ERR_THR or float(metrics.get("p95", 0.0)) >= P95_THR:
            return True
    except Exception:
        pass
    return False


def render_line(topic: str, data: dict, mal: bool) -> str:
    ts = int(data.get("ts", time.time()))
    line = {"ts": ts, "topic": topic, "data": data}
    out = json.dumps(line, separators=(",", ":"))
    if not COLOR:
        return out
    if mal:
        return f"{RED}{out}{RESET}"
    if topic.startswith("sentinel/health"):
        return f"{DIM}{GREEN}{out}{RESET}"
    return f"{CYAN}{out}{RESET}"


async def run():
    u = urlparse(MQTT_URL)
    host = u.hostname or "localhost"
    port = u.port or 1883
    while True:
        try:
            async with Client(host, port) as client:
                await client.subscribe("sentinel/#")
                async with client.messages() as messages:
                    async for msg in messages:
                        topic = str(getattr(msg.topic, "value", msg.topic))
                        try:
                            data = orjson.loads(msg.payload)
                        except Exception:
                            try:
                                data = {"raw": msg.payload.decode("utf-8", "ignore")}
                            except Exception:
                                data = {"raw": str(msg.payload)}
                        mal = classify(topic, data)
                        if not VERBOSE and not mal:
                            continue
                        print(render_line(topic, data, mal), flush=True)
        except Exception:
            await asyncio.sleep(1)


if __name__ == "__main__":
    import uvloop
    uvloop.install()
    asyncio.run(run())
