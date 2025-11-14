"""
Local smoke test without Azure Functions host.
It calls the same handlers used by HTTP/Queue functions and produces stats.
"""
import json
from functions.ingest_sensors import __init__ as ingest
from functions.process_stats import __init__ as proc
from common import db as dbmod

def run_once(n_sensors=100, n_samples=100, seed=42):
    r = ingest.handler(n_sensors, n_samples, seed)
    # simulate queue trigger
    res = proc.handler({"batch_id": r["batch_id"]})
    return r, res

def main():
    dbmod.init_db()
    sizes = [(50,50), (100,50), (200,50), (500,50), (1000, 20)]
    for s, k in sizes:
        r, res = run_once(n_sensors=s, n_samples=k, seed=42)
        print(json.dumps({
            "sensors": s,
            "samples": k,
            "ingest_ms": r["duration_ms"],
            "process_ms": res["duration_ms"],
            "rows": r["rows"]
        }))

if __name__ == "__main__":
    main()
