from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_STATE_BY_ACTION = {
    "store_normal_sample": "archived_normal",
    "accept_prediction": "accepted_prediction",
    "predict_and_monitor": "monitoring_prediction",
    "request_user_label": "awaiting_label_review",
    "review_mask_quality": "monitoring_mask_quality",
    "request_mask_feedback": "awaiting_mask_feedback",
}

TASK_PRIORITY_BY_ACTION = {
    "store_normal_sample": "low",
    "accept_prediction": "low",
    "predict_and_monitor": "medium",
    "request_user_label": "high",
    "review_mask_quality": "medium",
    "request_mask_feedback": "high",
}

TASK_QUEUE_BY_ACTION = {
    "store_normal_sample": "normal_archive",
    "accept_prediction": "completed",
    "predict_and_monitor": "monitoring",
    "request_user_label": "human_review",
    "review_mask_quality": "quality_watchlist",
    "request_mask_feedback": "annotation_review",
}

LOW_CONFIDENCE_REVIEW_THRESHOLD = 0.70
WEAK_MASK_REVIEW_THRESHOLD = 0.45


def _confidence_band(confidence: float) -> str:

    if confidence >= 0.85:
        return "high"
    if confidence >= LOW_CONFIDENCE_REVIEW_THRESHOLD:
        return "medium"
    return "low"


def _quality_band(metrics: dict[str, Any] | None) -> str:

    if not metrics:
        return "unknown"

    iou = float(metrics.get("iou", 0.0))

    if iou >= 0.60:
        return "strong"
    if iou >= 0.30:
        return "moderate"
    return "weak"


def _read_jsonl_records(path: Path, limit: int | None = None) -> list[dict[str, Any]]:

    if not path.exists():
        return []

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(payload, dict):
                records.append(payload)

    if limit is not None and limit > 0:
        return records[-limit:]

    return records


def _append_jsonl_record(path: Path, payload: dict[str, Any]) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _parse_timestamp(raw_value: Any) -> datetime | None:

    if not raw_value or not isinstance(raw_value, str):
        return None

    normalized = raw_value.strip().replace("Z", "+00:00")

    for candidate in (normalized, normalized.replace(" ", "T")):
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError:
            continue

    return None


def _latest_successful_retrain(logs_dir: Path) -> datetime | None:

    retrain_records = _read_jsonl_records(logs_dir / "retrain_history.jsonl")
    successful_retrains = [
        record for record in retrain_records
        if record.get("status") == "completed"
    ]

    if not successful_retrains:
        return None

    return _parse_timestamp(successful_retrains[-1].get("timestamp"))


def _workflow_snapshot(base_dir: str) -> dict[str, Any]:

    logs_dir = Path(base_dir) / "logs"
    last_retrain_at = _latest_successful_retrain(logs_dir)

    prediction_records = _read_jsonl_records(logs_dir / "predictions.json", limit=80)
    feedback_records = _read_jsonl_records(logs_dir / "feedback.jsonl", limit=80)
    task_records = _read_jsonl_records(logs_dir / "agent_tasks.jsonl", limit=120)

    evaluation_predictions = []
    for record in prediction_records:
        prediction_timestamp = _parse_timestamp(record.get("timestamp"))
        if last_retrain_at is None or (
            prediction_timestamp is not None and prediction_timestamp > last_retrain_at
        ):
            evaluation_predictions.append(record)

    new_feedback_records = []
    for record in feedback_records:
        feedback_timestamp = _parse_timestamp(record.get("timestamp"))
        if last_retrain_at is None or (
            feedback_timestamp is not None and feedback_timestamp > last_retrain_at
        ):
            new_feedback_records.append(record)

    action_counter: Counter[str] = Counter()
    defect_counter: Counter[str] = Counter()
    state_counter: Counter[str] = Counter()
    low_confidence_count = 0
    weak_quality_count = 0

    for record in evaluation_predictions:
        action = record.get("agent_action")
        prediction = record.get("prediction") or {}
        defect_type = prediction.get("defect_type")
        confidence = float(record.get("confidence") or 0.0)
        metrics = record.get("metrics") or {}

        if action:
            action_counter[str(action)] += 1

        if defect_type:
            defect_counter[str(defect_type)] += 1

        if confidence < LOW_CONFIDENCE_REVIEW_THRESHOLD:
            low_confidence_count += 1

        iou = metrics.get("iou")
        if iou is not None and float(iou) < WEAK_MASK_REVIEW_THRESHOLD:
            weak_quality_count += 1

    for task in task_records:
        task_timestamp = _parse_timestamp(task.get("timestamp"))
        if last_retrain_at is not None and task_timestamp is not None and task_timestamp <= last_retrain_at:
            continue

        state = task.get("task_state")
        if state:
            state_counter[str(state)] += 1

    total_predictions = len(evaluation_predictions)
    low_confidence_rate = low_confidence_count / total_predictions if total_predictions else 0.0
    weak_quality_rate = weak_quality_count / total_predictions if total_predictions else 0.0

    return {
        "last_successful_retrain_at": last_retrain_at.isoformat() if last_retrain_at else None,
        "prediction_window_size": total_predictions,
        "new_feedback_count": len(new_feedback_records),
        "low_confidence_count": low_confidence_count,
        "weak_quality_count": weak_quality_count,
        "low_confidence_rate": round(low_confidence_rate, 4),
        "weak_quality_rate": round(weak_quality_rate, 4),
        "recent_action_breakdown": dict(action_counter),
        "recent_defect_breakdown": dict(defect_counter),
        "task_state_breakdown": dict(state_counter),
        "top_defect_under_watch": defect_counter.most_common(1)[0][0] if defect_counter else None,
    }


def _record_agent_task(base_dir: str, source_filename: str | None, task_entry: dict[str, Any]) -> None:

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_filename": source_filename,
        **task_entry,
    }
    _append_jsonl_record(Path(base_dir) / "logs" / "agent_tasks.jsonl", payload)


def _build_rule_based_plan(
    *,
    prediction: dict[str, Any],
    confidence: float,
    anomaly_score: float | None,
    anomaly_threshold: float | None,
    metrics: dict[str, Any] | None,
    has_ground_truth: bool,
) -> dict[str, Any]:

    status = prediction.get("status", "unknown")
    defect_type = prediction.get("defect_type")
    confidence_level = _confidence_band(confidence)
    quality_level = _quality_band(metrics)

    reasoning = [
        "Image processed by classifier and anomaly detector.",
    ]
    next_steps: list[str] = []
    automated_tasks: list[str] = ["prediction_logged"]
    alerts: list[str] = []

    if status == "normal":
        reasoning.append("Anomaly score is below the defect threshold, so the sample is treated as normal.")
        action = "store_normal_sample"
        summary = "Agent accepted this image as a normal wood sample."
        next_steps.append("Store this image in the normal-sample history for later review.")
    else:
        reasoning.append(
            f"Predicted defect type is '{defect_type}' with {confidence_level} confidence."
        )

        if anomaly_score is not None and anomaly_threshold is not None:
            reasoning.append(
                f"Anomaly score {anomaly_score:.2f} was compared against threshold {anomaly_threshold:.2f}."
            )

        if confidence_level == "low":
            action = "request_user_label"
            summary = "Agent routed this sample for human review because the classification confidence is low."
            alerts.append("Low-confidence prediction")
            automated_tasks.append("feedback_requested")
            next_steps.append("Ask the user to confirm the defect type and submit feedback.")
            next_steps.append("Use the reviewed sample during retraining.")
        elif not has_ground_truth:
            action = "predict_and_monitor"
            summary = "Agent accepted the predicted defect type and marked the sample for monitoring because no ground truth is available."
            automated_tasks.append("queued_for_monitoring")
            next_steps.append("Show the predicted defect type to the user.")
            next_steps.append("Collect feedback if the prediction looks incorrect.")
        elif quality_level == "strong":
            action = "accept_prediction"
            summary = "Agent accepted the prediction because localization quality is strong."
            automated_tasks.append("high_quality_prediction_logged")
            next_steps.append("Use this result as a reliable example in the dashboard history.")
        elif quality_level == "moderate":
            action = "review_mask_quality"
            summary = "Agent accepted the defect type but flagged the mask quality for monitoring."
            alerts.append("Mask quality is moderate")
            automated_tasks.append("mask_quality_monitored")
            next_steps.append("Keep the predicted defect type.")
            next_steps.append("Monitor repeated mask drift for this defect class.")
        else:
            action = "request_mask_feedback"
            summary = "Agent detected a likely defect but the localization quality is weak, so it is asking for corrective feedback."
            alerts.append("Weak localization quality")
            automated_tasks.append("mask_feedback_requested")
            next_steps.append("Ask the user to refine the defect region.")
            next_steps.append("Use the corrected region in the feedback dataset.")

    if has_ground_truth:
        reasoning.append("Ground-truth comparison was available for quality evaluation.")
    else:
        reasoning.append("Ground-truth comparison was not available for this upload.")

    return {
        "mode": "rule_based_agent",
        "action": action,
        "summary": summary,
        "confidence_level": confidence_level,
        "quality_level": quality_level,
        "alerts": alerts,
        "reasoning": reasoning,
        "next_steps": next_steps,
        "automated_tasks": automated_tasks,
    }


def build_agent_plan(
    *,
    prediction: dict[str, Any],
    confidence: float,
    anomaly_score: float | None,
    anomaly_threshold: float | None,
    metrics: dict[str, Any] | None,
    has_ground_truth: bool,
    evaluation_model: str | None = None,
    base_dir: str | None = None,
    source_filename: str | None = None,
) -> dict[str, Any]:

    rule_plan = _build_rule_based_plan(
        prediction=prediction,
        confidence=confidence,
        anomaly_score=anomaly_score,
        anomaly_threshold=anomaly_threshold,
        metrics=metrics,
        has_ground_truth=has_ground_truth,
    )

    task_state = TASK_STATE_BY_ACTION[rule_plan["action"]]
    task_priority = TASK_PRIORITY_BY_ACTION[rule_plan["action"]]
    queue_name = TASK_QUEUE_BY_ACTION[rule_plan["action"]]

    workflow_memory = _workflow_snapshot(base_dir) if base_dir else {
        "prediction_window_size": 0,
        "new_feedback_count": 0,
        "low_confidence_rate": 0.0,
        "weak_quality_rate": 0.0,
        "recent_action_breakdown": {},
        "recent_defect_breakdown": {},
        "task_state_breakdown": {},
        "top_defect_under_watch": None,
        "last_successful_retrain_at": None,
    }

    workflow_reasoning = [
        f"Task state assigned as '{task_state}' in queue '{queue_name}'.",
    ]
    workflow_next_steps = [
        f"Keep this sample in the '{queue_name}' workflow bucket until the next agent review cycle."
    ]

    if workflow_memory["new_feedback_count"] > 0:
        workflow_reasoning.append(
            f"{workflow_memory['new_feedback_count']} feedback samples are waiting since the last retraining cycle."
        )

    if workflow_memory["weak_quality_rate"] >= 0.20:
        workflow_reasoning.append(
            f"Weak mask quality is trending at {workflow_memory['weak_quality_rate']:.0%} in the active review window."
        )
        workflow_next_steps.append("Prioritize mask-quality monitoring before the next retraining decision.")

    if workflow_memory["low_confidence_rate"] >= 0.20:
        workflow_reasoning.append(
            f"Low-confidence cases are trending at {workflow_memory['low_confidence_rate']:.0%} in the active review window."
        )
        workflow_next_steps.append("Collect more human-confirmed labels for uncertain samples.")

    top_defect_under_watch = workflow_memory.get("top_defect_under_watch")
    if top_defect_under_watch:
        workflow_reasoning.append(
            f"Recent active monitoring is concentrated around '{top_defect_under_watch}' samples."
        )

    workflow_manager = {
        "available": True,
        "review_source": "local_workflow",
        "status": "active",
        "summary": (
            f"Local workflow controller placed this sample in '{task_state}' with {task_priority} priority."
        ),
        "reasoning": workflow_reasoning,
        "next_steps": workflow_next_steps,
        "task_state": task_state,
        "task_priority": task_priority,
        "queue_name": queue_name,
        "memory_snapshot": workflow_memory,
    }

    task_entry = {
        "task_state": task_state,
        "task_priority": task_priority,
        "queue_name": queue_name,
        "action": rule_plan["action"],
        "confidence_level": rule_plan["confidence_level"],
        "quality_level": rule_plan["quality_level"],
        "prediction": prediction,
    }

    if base_dir and source_filename:
        _record_agent_task(base_dir, source_filename, task_entry)

    return {
        **rule_plan,
        "mode": "agent_workflow_controller",
        "review_source": "local_workflow",
        "workflow_state": task_state,
        "workflow_priority": task_priority,
        "workflow_queue": queue_name,
        "rule_based_plan": rule_plan,
        "workflow_manager": workflow_manager,
    }


def build_agent_review(base_dir: str, limit: int = 100) -> dict[str, Any]:

    logs_dir = Path(base_dir) / "logs"
    workflow_memory = _workflow_snapshot(base_dir)
    task_records = _read_jsonl_records(logs_dir / "agent_tasks.jsonl", limit=limit)
    last_retrain_at = _parse_timestamp(workflow_memory.get("last_successful_retrain_at"))

    active_task_counter: Counter[str] = Counter()
    for task in task_records[-limit:]:
        task_timestamp = _parse_timestamp(task.get("timestamp"))
        if last_retrain_at is not None and task_timestamp is not None and task_timestamp <= last_retrain_at:
            continue

        queue_name = task.get("queue_name")
        if queue_name and queue_name not in {"completed", "normal_archive"}:
            active_task_counter[str(queue_name)] += 1

    total_predictions = int(workflow_memory.get("prediction_window_size", 0))
    low_confidence_rate = float(workflow_memory.get("low_confidence_rate", 0.0))
    weak_quality_rate = float(workflow_memory.get("weak_quality_rate", 0.0))
    new_feedback_count = int(workflow_memory.get("new_feedback_count", 0))

    recommendation = "continue_monitoring"
    reasons: list[str] = []
    next_steps: list[str] = []

    if total_predictions == 0:
        recommendation = "collect_more_data"
        reasons.append("No prediction logs are available yet in the current post-retraining review window.")
        next_steps.append("Run more sample predictions so the agent can evaluate current model behavior.")
    else:
        if low_confidence_rate >= 0.25:
            reasons.append(
                f"Low-confidence predictions are {low_confidence_rate:.0%} of the active review window."
            )
        if weak_quality_rate >= 0.20:
            reasons.append(
                f"Weak localization quality appears in {weak_quality_rate:.0%} of the active review window."
            )
        if new_feedback_count >= 3:
            reasons.append(
                f"{new_feedback_count} feedback samples are queued since the last retraining cycle."
            )
        if active_task_counter:
            busiest_queue = active_task_counter.most_common(1)[0]
            reasons.append(
                f"The busiest agent queue is '{busiest_queue[0]}' with {busiest_queue[1]} active samples."
            )

        if new_feedback_count >= 3 or low_confidence_rate >= 0.25 or weak_quality_rate >= 0.20:
            recommendation = "start_retraining"
            next_steps.append("Start retraining once you are ready to incorporate the queued review data.")
            next_steps.append("After retraining, check whether the active queue sizes decrease.")
        else:
            next_steps.append("Keep collecting production predictions and feedback.")
            next_steps.append("Use the workflow queues to prioritize which samples need attention first.")

    summary = {
        "total_predictions": total_predictions,
        "prediction_window_resets_after_retrain": workflow_memory.get("last_successful_retrain_at") is not None,
        "total_feedback": len(_read_jsonl_records(logs_dir / "feedback.jsonl", limit=limit)),
        "new_feedback_since_last_retrain": new_feedback_count,
        "low_confidence_count": workflow_memory.get("low_confidence_count", 0),
        "weak_quality_count": workflow_memory.get("weak_quality_count", 0),
        "low_confidence_rate": round(low_confidence_rate, 4),
        "weak_quality_rate": round(weak_quality_rate, 4),
        "top_predicted_defect": workflow_memory.get("top_defect_under_watch"),
        "top_feedback_label": None,
        "last_successful_retrain_at": workflow_memory.get("last_successful_retrain_at"),
        "action_breakdown": workflow_memory.get("recent_action_breakdown", {}),
        "defect_breakdown": workflow_memory.get("recent_defect_breakdown", {}),
        "feedback_breakdown": dict(Counter(
            record.get("label")
            for record in _read_jsonl_records(logs_dir / "feedback.jsonl", limit=limit)
            if record.get("label")
        )),
        "task_queue_breakdown": dict(active_task_counter),
    }

    return {
        "mode": "agent_review_loop",
        "review_window": limit,
        "recommendation": recommendation,
        "summary": summary,
        "reasons": reasons,
        "next_steps": next_steps,
    }
