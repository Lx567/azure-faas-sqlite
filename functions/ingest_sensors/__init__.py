import json, time, uuid, random, datetime, tracemalloc
try:
    import azure.functions as func
except Exception:
    func = None  # allow local import without azure

from common import db as dbmod  # type: ignore
from common import config  # type: ignore

def simulate_readings(n_sensors:int, n_samples:int, seed:int=None):
    rnd = random.Random(seed)
    now = datetime.datetime.utcnow()
    rows = []
    for s in range(n_sensors):
        base_t = rnd.uniform(18, 26)
        base_c = rnd.uniform(400, 800)
        base_h = rnd.uniform(30, 60)
        for i in range(n_samples):
            ts = now + datetime.timedelta(seconds=i)
            temp = base_t + rnd.uniform(-2, 2)
            co2  = base_c + rnd.uniform(-50, 50)
            hum  = base_h + rnd.uniform(-5, 5)
            rows.append((s, ts.isoformat() + "Z", temp, co2, hum))
    return rows

def handler(n_sensors:int, n_samples:int, seed:int=None):
    invocation_id = str(uuid.uuid4())
    start = time.perf_counter()
    tracemalloc.start()
    db = dbmod.init_db()
    cur = db.cursor()
    batch_id = str(uuid.uuid4())
    rows = simulate_readings(n_sensors, n_samples, seed)
    cur.executemany(
        "INSERT INTO readings(batch_id, sensor_id, ts, temperature, co2, humidity) VALUES (?, ?, ?, ?, ?, ?)",
        [(batch_id, s, ts, t, c, h) for (s, ts, t, c, h) in rows]
    )
    db.commit()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end = time.perf_counter()
    duration_ms = (end - start) * 1000.0
    cur.execute("""
        INSERT INTO metrics(func_name, invocation_id, start_ts, end_ts, duration_ms, cpu_user, cpu_system, rss_mb, peak_py_mb, extra)
        VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
    """, ("ingest_sensors", invocation_id, datetime.datetime.utcnow().isoformat()+"Z",
          datetime.datetime.utcnow().isoformat()+"Z", duration_ms, peak/1024/1024, json.dumps({"batch_id": batch_id, "n_rows": len(rows)})))
    db.commit()
    return {"ok": True, "batch_id": batch_id, "rows": len(rows), "duration_ms": duration_ms}

# Azure Functions entrypoint
async def main(req):  # type: ignore
    try:
        data = req.get_json()
    except Exception:
        data = {}
    n_sensors = int(data.get("sensors", req.params.get("sensors", config.DEFAULT_SENSORS)))
    n_samples = int(data.get("samples", req.params.get("samples", config.DEFAULT_SAMPLES)))
    seed = data.get("seed", None)
    result = handler(n_sensors, n_samples, seed)
    if func:
        return func.HttpResponse(json.dumps(result), status_code=200, mimetype="application/json")
    return json.dumps(result)
