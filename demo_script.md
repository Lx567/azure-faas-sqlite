# 2 分钟演示脚本（提词）
1. 开场（10s）：说明目标与两函数工作流（HTTP → 队列），展示架构图。
2. 本地仿真（30s）：运行 `python scripts/simulate_local.py`，展示生成的 `batch_id`、数据库文件与 `stats` 表。
3. 启动函数宿主（20s）：`func start`，用 `curl` 触发 `/api/ingest`，展示响应。
4. 队列触发（20s）：用 `az storage message put` 推送 `batch_id` 消息，查看日志中 process 函数输出。
5. 性能结果（20s）：打开 `results/*.png` 简要解读“近似线性扩展”。
6. 收尾（20s）：总结改进方向（换 Azure SQL、启用 Application Insights、Premium 计划）。
