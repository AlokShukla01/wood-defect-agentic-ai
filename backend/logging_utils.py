import json
from datetime import datetime
from pathlib import Path


def append_prediction_log(base_dir, result, source_filename=None):
    log_path = Path(base_dir) / "logs" / "predictions.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_filename": source_filename,
        "prediction": result.get("prediction"),
        "confidence": result.get("confidence"),
        "anomaly_score": result.get("anomaly_score"),
        "evaluation_model": result.get("evaluation_model"),
        "agent_action": result.get("agent_action"),
        "metrics": result.get("metrics")
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")

    return True
