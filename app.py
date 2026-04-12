import asyncio
import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

from main import DataPipeline
from pipeline import load_config, setup_logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

status = {
    "state": "idle",
    "last_run": None,
    "message": "Ready",
    "output_dir": os.environ.get("OUTPUT_DIR", "output"),
}
status_lock = threading.Lock()


def get_config_path() -> Path:
    return Path(os.environ.get("PIPELINE_CONFIG", "config.yaml"))


def update_status(state: str, message: str, last_run: str = None):
    with status_lock:
        status["state"] = state
        status["message"] = message
        if last_run is not None:
            status["last_run"] = last_run


def pipeline_runner(company_slugs=None):
    try:
        update_status("running", "Pipeline started")
        config_path = get_config_path()
        setup_logging(os.environ.get("LOG_LEVEL", "INFO").upper())
        config = load_config(config_path)

        pipeline = DataPipeline(config)
        asyncio.run(pipeline.run(company_slugs))

        update_status(
            "idle",
            "Pipeline completed successfully",
            datetime.utcnow().isoformat() + "Z",
        )
    except Exception as exc:
        logger.exception("Pipeline run failed")
        update_status(
            "error",
            f"Pipeline failed: {exc}",
            datetime.utcnow().isoformat() + "Z",
        )


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.get("/")
def index():
    return jsonify(status)


@app.get("/status")
def status_route():
    return jsonify(status)


@app.post("/run")
def run_pipeline():
    if status["state"] == "running":
        return jsonify({"error": "Pipeline already running"}), 409

    company_slugs = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        company_slugs = payload.get("companies")
        if company_slugs is not None and not isinstance(company_slugs, list):
            return jsonify({"error": "companies must be a list"}), 400

    thread = threading.Thread(
        target=pipeline_runner,
        args=(company_slugs,),
        daemon=True,
    )
    thread.start()

    return jsonify({"status": "started", "companies": company_slugs}), 202


@app.get("/report")
def get_report():
    report_path = Path(status["output_dir"]) / "coverage.json"
    if not report_path.exists():
        return jsonify({"error": "Report not found"}), 404

    try:
        with report_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as exc:
        logger.exception("Failed to read report")
        return jsonify({"error": f"Failed to read report: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
