# 课程作业报告：基于 Azure Functions 的无服务器工作流（Python + SQLite）

## 1. 场景与目标
选择 **IoT 环境监测** 场景：N 个传感器周期性产生温度、CO₂、湿度数据。我们实现了两函数工作流：
- **函数 A（ingest_sensors，HTTP 触发）**：模拟传感器数据，批量落库至 SQLite，并输出 `batch_id`。
- **函数 B（process_stats，队列触发）**：按批次聚合最小/最大/均值，写入 `stats` 表。

目标：展示在无服务器平台下的工作流实现、自动化衔接与可扩展性，并从运行时间与内存角度进行性能评测。

## 2. 方案设计
- **触发机制**：采用「HTTP→队列」链路使批处理可控、易扩展。与 Azure SQL 触发器思路一致，我们将“变更事件”外显为队列消息，以便本次作业采用 SQLite 也能复现「数据入库→自动计算」的流程。
- **数据层**：按要求使用 SQLite；函数并发时启用 `WAL` 模式以改善读写并发体验。
- **幂等与进度**：`control` 表记录已处理的最大 `readings.id`，支持无 `batch_id` 情形下的增量扫描。
- **可扩展性**：通过增大 `sensors` × `samples` 与并发调用次数，观察吞吐与时延变化；若迁移至 Azure SQL，可利用分区与并行化进一步扩展。

### 架构
```
Client ──HTTP──> Function A (ingest_sensors) ──enqueue──> Queue ──trigger──> Function B (process_stats)
                                  │                                      │
                               SQLite (readings, metrics)           SQLite (stats, control, metrics)
```

## 3. 实现概述（Python）
- 关键代码：`functions/ingest_sensors/__init__.py`、`functions/process_stats/__init__.py`、`common/db.py`。
- **函数 A** 批量写入 `readings`，记录运行时间与 Python 层峰值内存（`tracemalloc`）。
- **函数 B** 按批聚合三类指标（温度/CO₂/湿度），并记录自身性能指标。
- **脚本**：`scripts/simulate_local.py`（本地仿真），`scripts/benchmark.py`（HTTP 压测）。

## 4. 评测方法
- **数据规模**：传感器数 `s` ∈ {50, 100, 200, 500, 1000}；每个传感器样本数 `k` ∈ {50}（或 20）。
- **指标**：函数内部 `duration_ms`；Python 层峰值内存（MB）。
- **环境**：本地仿真（等价算法/数据路径）；若在 Azure，可使用相同代码并启用 Application Insights 与 `psutil` 收集 RSS/CPU。

## 5. 结果摘要（示例）
详见 `results/` 图表。趋势：
- **ingest** 随数据量近似线性增长；
- **process** 聚合阶段对行数敏感但常低于写入阶段；
- 内存峰值随批量上升，未见异常陡增。

## 6. 讨论
- **冷启动**：消费计划中冷启动会增加 p95 延迟；可通过预热（定时触发）或切换到 Premium 计划缓解。
- **SQLite 的局限**：单文件 DB 对高并发与跨实例扩展有限制；迁移到 Azure SQL/队列原语能更好支撑规模化。
- **触发器选择**：若使用 Azure SQL，可用变更订阅或 CDC + 触发函数；本次以队列替代复现“数据变更 → 统计”的语义。

## 7. 结论
本作业完成了两函数无服务器工作流的设计与实现，给出本地与云端的运行指导与性能基线。代码可直接部署并扩展至真实 Azure 环境。
