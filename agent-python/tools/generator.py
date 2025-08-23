import argparse, json, os, random, time
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--log", default="/data/rpc.jsonl")
parser.add_argument("--rate", type=int, default=400)  # events/sec
parser.add_argument("--burst", default="getProgramAccounts")
parser.add_argument("--err", type=float, default=0.02)  # error rate în burst
parser.add_argument("--baseline_lat", type=float, default=90)     # <- FIX
parser.add_argument("--burst_lat", type=float, default=260)       # <- FIX
parser.add_argument("--burst_secs", type=int, default=20)
args = parser.parse_args()

methods = ["getProgramAccounts", "getLogs", "getBalance", "getBlock"]
ips = [f"10.0.0.{i}" for i in range(2, 200)]

def one_event(burst=False):
    m = random.choices(methods, weights=[4, 3, 2, 1])[0]
    if burst:
        m = args.burst
    lat = random.gauss(args.baseline_lat, 15)            # <- FIX
    if burst and m == args.burst:
        lat = random.gauss(args.burst_lat, 35)           # <- FIX
    status = 200
    if burst and random.random() < args.err:
        status = random.choice([500, 502, 503])
    return {
        "time": datetime.utcnow().isoformat() + "Z",
        "ip": random.choice(ips),
        "method": m,
        "lat_ms": max(1, lat),
        "status": status,
    }

with open(args.log, "a", buffering=1) as f:
    print(f"# writing JSONL to {args.log}")
    t0 = time.time()
    while True:
        burst = (int(time.time() - t0) // (args.burst_secs * 2)) % 2 == 1
        for _ in range(args.rate):
            ev = one_event(burst)
            f.write(json.dumps(ev) + "\n")
        time.sleep(1.0)
