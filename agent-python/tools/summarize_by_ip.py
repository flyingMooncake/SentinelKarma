import argparse, os, sys, json, re
from typing import Dict, Any

try:
    import orjson as _json
    def jloads(b: bytes):
        return _json.loads(b)
    def jdumps(o: Any):
        return _json.dumps(o)
except Exception:
    import json as _json
    def jloads(b: bytes):
        return _json.loads(b)
    def jdumps(o: Any):
        return _json.dumps(o).encode()


def sanitize_name(s: str) -> str:
    # Safe-ish for filenames; preserve hex
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def summarize(input_path: str, output_path: str, group_field: str, split_dir: str | None,
              zlat_thr: float, zerr_thr: float, p95_thr: float, err_thr: float) -> None:
    if not os.path.isfile(input_path):
        raise SystemExit(f"Input file not found: {input_path}")

    # Aggregates by group key (IP or sample)
    agg: Dict[str, Dict[str, Any]] = {}

    # Optional per-IP split
    writers: Dict[str, Any] = {}
    try:
        with open(input_path, 'rb') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = jloads(line)
                except Exception:
                    # Skip malformed lines
                    continue

                # Determine key
                key = None
                if group_field in obj:
                    key = obj.get(group_field)
                elif group_field == 'ip' and isinstance(obj.get('sample'), str):
                    # If only hashed present, group by sample
                    key = obj.get('sample')
                else:
                    # Try nested monitor format {ts, topic, data}
                    data = obj.get('data') if isinstance(obj.get('data'), dict) else None
                    if data and group_field in data:
                        key = data.get(group_field)
                    elif data and group_field == 'ip' and isinstance(data.get('sample'), str):
                        key = data.get('sample')
                if not key:
                    # if still none, drop
                    continue
                key = str(key)

                # Classify attack subtype (latency vs error) and method
                data_obj = obj.get('data') if isinstance(obj.get('data'), dict) else obj
                z = data_obj.get('z') or {}
                metrics = data_obj.get('metrics') or {}
                method = data_obj.get('method') or 'unknown'

                lat_attack = False
                err_attack = False
                try:
                    if float(z.get('lat', 0.0)) >= zlat_thr or float(metrics.get('p95', 0.0)) >= p95_thr:
                        lat_attack = True
                except Exception:
                    pass
                try:
                    if float(z.get('err', 0.0)) >= zerr_thr or float(metrics.get('err_rate', 0.0)) >= err_thr:
                        err_attack = True
                except Exception:
                    pass

                g = agg.get(key)
                if g is None:
                    g = agg[key] = {
                        'ip': key,
                        'count': 0,
                        'methods': {},    # per-method counts
                        'types': {'latency': 0, 'error': 0},  # subtype counters
                    }
                g['count'] += 1
                g['methods'][method] = g['methods'].get(method, 0) + 1
                if lat_attack:
                    g['types']['latency'] += 1
                if err_attack:
                    g['types']['error'] += 1

                # Split logs by IP/sample if requested
                if split_dir:
                    os.makedirs(split_dir, exist_ok=True)
                    fname = sanitize_name(key) + '.log'
                    p = os.path.join(split_dir, fname)
                    w = writers.get(p)
                    if w is None:
                        w = open(p, 'ab', buffering=0)
                        writers[p] = w
                    w.write(line + b"\n")
    finally:
        for w in writers.values():
            try:
                w.flush()
            except Exception:
                pass
            try:
                w.close()
            except Exception:
                pass

    # Emit summary (sorted by count desc)
    summary = sorted(agg.values(), key=lambda x: x['count'], reverse=True)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'wb') as out:
        out.write(jdumps(summary))


def main():
    ap = argparse.ArgumentParser(description='Summarize malicious logs by IP (or hashed sample).')
    ap.add_argument('--input', required=True, help='Path to malicious log file (JSON lines)')
    ap.add_argument('--output', default='data/ip_summary.json', help='Where to write summary JSON')
    ap.add_argument('--group-field', default='sample', choices=['sample','ip'], help='Field name to group by (default: sample)')
    ap.add_argument('--split-dir', default=None, help='Optional: directory to write per-IP log files')
    ap.add_argument('--zlat-thr', type=float, default=float(os.getenv('ZLAT_THR', os.getenv('Z_THRESHOLD','3.0'))))
    ap.add_argument('--zerr-thr', type=float, default=float(os.getenv('ZERR_THR', os.getenv('Z_THRESHOLD','3.0'))))
    ap.add_argument('--p95-thr', type=float, default=float(os.getenv('P95_THR', '250')))
    ap.add_argument('--err-thr', type=float, default=float(os.getenv('ERR_THR', '0.05')))
    args = ap.parse_args()

    summarize(
        input_path=args.input,
        output_path=args.output,
        group_field=args.group_field,
        split_dir=args.split_dir,
        zlat_thr=args.zlat_thr,
        zerr_thr=args.zerr_thr,
        p95_thr=args.p95_thr,
        err_thr=args.err_thr,
    )

if __name__ == '__main__':
    main()
