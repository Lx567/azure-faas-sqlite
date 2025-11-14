# 无服务器工作流（Azure Functions + SQLite，Python）

> 两函数工作流：**数据采集/入库（HTTP 触发）** → **统计分析（队列触发）**。附本地仿真、基准脚本与性能结果图。

## 目录
- `functions/ingest_sensors`: 模拟 N 个传感器、写入 SQLite，并记录函数内部指标。
- `functions/process_stats`: 消费队列消息（以 `batch_id` 为粒度），聚合最小/最大/均值。
- `common/`: SQLite 工具与配置。
- `scripts/simulate_local.py`: 无需 Azure 主机的本地仿真。
- `scripts/benchmark.py`: 针对 HTTP 触发函数的并发压测。
- `results/`: 示例性能图表与 CSV。
- `data/serverless.db`: 运行时生成的 SQLite 文件。

## 快速开始（本地）
1. 安装 Azure Functions Core Tools 与 Python 3.10+。
2. 克隆本项目并安装依赖：
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. 先做一次本地仿真（无需启动函数宿主）：
   ```bash
   python scripts/simulate_local.py
   ```
4. 启动函数宿主（可选，用于 HTTP/队列联调）：
   ```bash
   func start
   # 另开终端：
   curl -X POST http://localhost:7071/api/ingest -H "content-type: application/json" -d '{"sensors":100,"samples":50}'
   ```
   收到 `batch_id` 后，手动向队列推送：
   ```bash
   az storage message put --queue-name stats-queue --content '{"batch_id":"<id>"}' --connection-string "UseDevelopmentStorage=true"
   ```

## 部署（Azure）
1. 创建资源组、存储账户与函数应用（Linux/Python）。
2. 配置应用设置：
   - `QUEUE_NAME=stats-queue`
   - `SQLITE_PATH=/home/site/wwwroot/data/serverless.db`
3. 部署：
   ```bash
   func azure functionapp publish <funcapp>
   ```

## 数据库模式
- `readings(batch_id, sensor_id, ts, temperature, co2, humidity)`
- `stats(batch_id, window_start, window_end, metric, min_val, max_val, avg_val, count_val)`
- `metrics(func_name, invocation_id, start_ts, end_ts, duration_ms, peak_py_mb, ...)`
- `control(k, v)`：标记已处理的最大 `readings.id`。

## 评测方法
- **可扩展性**：增大 `sensors` 与 `samples`，并用 `scripts/benchmark.py` 调整并发与调用次数。
- **运行时间**：函数内部记录 `duration_ms`；压测脚本记录端到端分位数。
- **资源消耗**：示例使用 `tracemalloc` 记录 Python 层峰值内存（MB）。在 Azure 上可改用 `psutil`/诊断器获取 RSS/CPU。

## 重要说明
- SQLite 适用于演示与单实例函数应用；生产场景建议替换为 Azure SQL/Cosmos DB，并使用事件/变更订阅触发第二函数。
