from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


class MetricsExporter:
    def __init__(self, db_path: str = "metrics/metrics.db") -> None:
        self.db_path = Path(db_path)

    def export_json(self, output_path: str) -> None:
        out = Path(output_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM task_metrics ORDER BY id DESC").fetchall()
        payload = [dict(row) for row in rows]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def export_csv(self, output_path: str) -> None:
        out = Path(output_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM task_metrics ORDER BY id DESC").fetchall()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "task", "success", "latency_ms", "model", "timestamp", "extra_json"])
            for row in rows:
                writer.writerow([row["id"], row["task"], row["success"], row["latency_ms"], row["model"], row["timestamp"], row["extra_json"]])
