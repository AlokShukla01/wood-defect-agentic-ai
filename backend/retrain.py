import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
import json


_retrain_lock = threading.Lock()
_retraining = False
_status_lock = threading.Lock()
_worker_thread = None
_retrain_status = {
    "state": "idle",
    "progress": 0,
    "current_epoch": 0,
    "total_epochs": 0,
    "message": "Retraining has not started.",
    "last_update": None,
    "started_at": None,
    "finished_at": None,
    "last_error": None,
}

_EPOCH_PATTERN = re.compile(r"Epoch\s+(\d+)/(\d+)")


def _update_status(**fields):

    with _status_lock:
        _retrain_status.update(fields)
        _retrain_status["last_update"] = datetime.utcnow().isoformat()


def get_retrain_status():

    with _status_lock:
        return dict(_retrain_status)


def start_retraining_job(base_dir, reload_callback=None):

    global _worker_thread

    if is_retraining():
        return False

    worker = threading.Thread(
        target=retrain_classifier,
        args=(base_dir, reload_callback),
        daemon=True
    )
    _worker_thread = worker
    worker.start()
    return True


def _write_retrain_history(base_dir, payload):

    log_path = Path(base_dir) / "logs" / "retrain_history.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def retrain_classifier(base_dir, reload_callback=None):

    global _retraining

    if not _retrain_lock.acquire(blocking=False):
        print("Retraining already in progress. Skipping duplicate request.")
        return False

    _retraining = True
    _update_status(
        state="running",
        progress=0,
        current_epoch=0,
        total_epochs=0,
        message="Retraining started.",
        started_at=datetime.utcnow().isoformat(),
        finished_at=None,
        last_error=None,
    )

    try:
        print("Agent triggering classifier retraining...")

        env = os.environ.copy()
        env["PYTHONPATH"] = base_dir
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen(
            [sys.executable, "-u", "training/train_classifier.py"],
            cwd=base_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        if process.stdout is not None:
            for raw_line in process.stdout:
                line = raw_line.strip()
                if not line:
                    continue

                print(line)

                epoch_match = _EPOCH_PATTERN.search(line)
                if epoch_match:
                    current_epoch = int(epoch_match.group(1))
                    total_epochs = int(epoch_match.group(2))
                    progress = int((current_epoch / max(1, total_epochs)) * 100)
                    _update_status(
                        current_epoch=current_epoch,
                        total_epochs=total_epochs,
                        progress=progress,
                        message=f"Training epoch {current_epoch}/{total_epochs} in progress.",
                    )
                elif "Best validation accuracy" in line:
                    _update_status(message=line)
                elif "Saved classifier" in line:
                    _update_status(message="Training finished. Saving the updated classifier.")

        return_code = process.wait()

        if return_code != 0:
            error_message = f"Classifier retraining failed with exit code {return_code}"
            print(error_message)
            _update_status(
                state="failed",
                progress=0,
                message=error_message,
                finished_at=datetime.utcnow().isoformat(),
                last_error=error_message,
            )
            _write_retrain_history(base_dir, {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "message": error_message,
            })
            return False

        if reload_callback is not None:
            reload_callback()

        print("Classifier retraining completed and model reloaded.")
        finished_at = datetime.utcnow().isoformat()
        _update_status(
            state="completed",
            progress=100,
            current_epoch=_retrain_status["total_epochs"],
            message="Classifier retraining completed and model reloaded.",
            finished_at=finished_at,
        )
        _write_retrain_history(base_dir, {
            "timestamp": finished_at,
            "status": "completed",
            "message": "Classifier retraining completed and model reloaded.",
            "total_epochs": _retrain_status["total_epochs"],
        })
        return True

    finally:
        _retraining = False
        _retrain_lock.release()


def is_retraining():

    return _retraining
