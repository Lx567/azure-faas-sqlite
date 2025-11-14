"""
Simple HTTP benchmarker for the ingest function when running the Azure Functions host locally or in Azure.
Usage:
  python scripts/benchmark.py --url http://localhost:7071/api/ingest --sensors 100 --samples 100 --concurrency 10 --runs 50
"""
import argparse, json, time, threading, queue, requests, statistics

def worker(q, url, results, payload):
    while True:
        try:
            i = q.get_nowait()
        except queue.Empty:
            return
        t0 = time.perf_counter()
        r = requests.post(url, json=payload, timeout=30)
        dt = (time.perf_counter() - t0) * 1000.0
        results.append(dt)
        q.task_done()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--sensors", type=int, default=100)
    p.add_argument("--samples", type=int, default=100)
    p.add_argument("--concurrency", type=int, default=10)
    p.add_argument("--runs", type=int, default=100)
    args = p.parse_args()
    payload = {"sensors": args.sensors, "samples": args.samples}
    q = queue.Queue()
    for i in range(args.runs):
        q.put(i)
    results = []
    threads = [threading.Thread(target=worker, args=(q, args.url, results, payload)) for _ in range(args.concurrency)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(json.dumps({
        "runs": args.runs,
        "concurrency": args.concurrency,
        "p50_ms": statistics.median(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(0.95*len(results))-1],
        "min_ms": min(results),
        "max_ms": max(results)
    }, indent=2))

if __name__ == "__main__":
    main()
