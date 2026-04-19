from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config.settings import AppConfig, load_config
from core.orchestrator import MultiAgentOrchestrator
from gui.main_window import MainWindow
from training_service.server import TrainingServer
from web.app import create_app

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Agent Coder System")
    parser.add_argument("--mode", choices=["gui", "cli", "web", "training_server"], default="gui")
    parser.add_argument("--task", default="", help="Task for CLI mode")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    return parser


def configure_logging(root: Path) -> None:
    logs_dir = root / "metrics"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / "app.log", encoding="utf-8"),
        ],
    )


def run_gui(config: AppConfig) -> int:
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow(config=config)
    window.show()
    return app.exec()


def run_cli(config: AppConfig, task: str) -> int:
    orchestrator = MultiAgentOrchestrator(config=config)
    result = orchestrator.solve(task)
    print(result.final_text)
    return 0


def run_web(config: AppConfig, host: str | None, port: int | None) -> int:
    import uvicorn

    app = create_app(config)
    uvicorn.run(app, host=host or config.web.host, port=port or config.web.port)
    return 0


def run_training_server(config: AppConfig) -> int:
    server = TrainingServer(config=config)
    server.serve_forever()
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    config = load_config(root)
    configure_logging(root)
    LOGGER.info("Starting in mode=%s", args.mode)

    if args.mode == "gui":
        return run_gui(config)
    if args.mode == "cli":
        if not args.task:
            parser.error("--task is required in cli mode")
        return run_cli(config, args.task)
    if args.mode == "web":
        return run_web(config, args.host, args.port)
    if args.mode == "training_server":
        return run_training_server(config)
    parser.error(f"Unsupported mode: {args.mode}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
