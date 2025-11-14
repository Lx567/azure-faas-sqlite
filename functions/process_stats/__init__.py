import json, time, uuid, datetime, tracemalloc
try:
    import azure.functions as func
except Exception:
    func = None  # allow local import

from common import db as dbmod  # type: ignore

def compute_stats(conn, batch_id:str=None):
    cur = conn.cursor()
    if batch_id:
        cur.execute("SELECT id, temperature, co2, humidity, ts FROM readings WHERE batch_id=? ORDER BY id", (batch_id,))
    else:
        last_id = dbmod.get_last_processed_id(conn)
        cur.execute("SELECT id, temperature, co2, humidity, ts, batch_id FROM readings WHERE id>? ORDER BY id", (last_id,))
    rows = cur.fetchall()
    if not rows:
        return None

    # Group by batch_id
    by_batch = {}
    for row in rows:
        if batch_id:
            id_, t, c, h, ts = row
            b = batch_id
        else:
            id_, t, c, h, ts, b = row
        by_batch.setdefault(b, []).append((id_, t, c, h, ts))

    for b, items in by_batch.items():
        ids = [r[0] for r in items]
        t_vals = [r[1] for r in items]
        c_vals = [r[2] for r in items]
        h_vals = [r[3] for r in items]
        ts_vals = [r[4] for r in items]
        window_start = min(ts_vals)
        window_end = max(ts_vals)
        def emit(metric, vals):
            cur.execute("""
                INSERT INTO stats(batch_id, window_start, window_end, metric, min_val, max_val, avg_val, count_val)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (b, window_start, window_end, metric, min(vals), max(vals), sum(vals)/len(vals), len(vals)))
        emit("temperature", t_vals)
        emit("co2", c_vals)
        emit("humidity", h_vals)
        dbmod.set_last_processed_id(conn, max(ids))
    conn.commit()
    return {"batches": list(by_batch.keys()), "rows": len(rows)}

def handler(message_body:dict):
    invocation_id = str(uuid.uuid4())
    start = time.perf_counter()
    tracemalloc.start()
    conn = dbmod.init_db()
    res = compute_stats(conn, batch_id=message_body.get("batch_id"))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end = time.perf_counter()
    duration_ms = (end - start) * 1000.0
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO metrics(func_name, invocation_id, start_ts, end_ts, duration_ms, cpu_user, cpu_system, rss_mb, peak_py_mb, extra)
        VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
    """, ("process_stats", invocation_id, datetime.datetime.utcnow().isoformat()+"Z",
          datetime.datetime.utcnow().isoformat()+"Z", duration_ms, peak/1024/1024, json.dumps(res or {})))
    conn.commit()
    return {"ok": True, "result": res, "duration_ms": duration_ms}

# Azure Queue trigger entry
def main(msg):  # type: ignore
    if func:
        body = msg.get_body().decode("utf-8")
        try:
            data = json.loads(body)
        except Exception:
            data = {"batch_id": None}
        handler(data)
    else:
        return None
