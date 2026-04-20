from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class TaskMetric:
    task: str
    success: bool
    latency_ms: float
    model: str
    timestamp: str
    extra: dict[str, Any]


class MetricsCollector:
    def __init__(self, db_path: str = "metrics/metrics.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    model TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    extra_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def record(
        self,
        task: str,
        success: bool,
        latency_ms: float,
        model: str,
        extra: dict[str, Any] | None = None,
    ) -> TaskMetric:
        payload = TaskMetric(
            task=task,
            success=success,
            latency_ms=latency_ms,
            model=model,
            timestamp=datetime.now(UTC).isoformat(),
            extra=extra or {},
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO task_metrics(task, success, latency_ms, model, timestamp, extra_json) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    payload.task,
                    1 if payload.success else 0,
                    payload.latency_ms,
                    payload.model,
                    payload.timestamp,
                    json.dumps(payload.extra, ensure_ascii=False),
                ),
            )
            conn.commit()
        return payload

    def recent(self, limit: int = 100) -> list[TaskMetric]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT task, success, latency_ms, model, timestamp, extra_json FROM task_metrics ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result: list[TaskMetric] = []
        for row in rows:
            result.append(
                TaskMetric(
                    task=row["task"],
                    success=bool(row["success"]),
                    latency_ms=float(row["latency_ms"]),
                    model=row["model"],
                    timestamp=row["timestamp"],
                    extra=json.loads(row["extra_json"]),
                )
            )
        return result
