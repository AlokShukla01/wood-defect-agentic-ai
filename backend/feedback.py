import base64
import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


ALLOWED_LABELS = {"color", "combined", "hole", "liquid", "scratch"}


def decode_image_bytes(file_bytes):

    np_arr = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Unable to decode uploaded image.")

    return image


def parse_bbox(raw_bbox):

    if not raw_bbox:
        return None

    if isinstance(raw_bbox, str):
        bbox = json.loads(raw_bbox)
    else:
        bbox = raw_bbox

    if not isinstance(bbox, dict):
        return None

    return bbox


def crop_from_bbox(image, bbox):

    if not bbox:
        return image

    height, width = image.shape[:2]

    x = float(bbox.get("x", 0))
    y = float(bbox.get("y", 0))
    crop_width = float(bbox.get("width", width))
    crop_height = float(bbox.get("height", height))
    unit = bbox.get("unit", "px")

    if unit == "%":
        x = width * x / 100.0
        y = height * y / 100.0
        crop_width = width * crop_width / 100.0
        crop_height = height * crop_height / 100.0

    x1 = max(0, min(width - 1, int(round(x))))
    y1 = max(0, min(height - 1, int(round(y))))
    x2 = max(x1 + 1, min(width, int(round(x + crop_width))))
    y2 = max(y1 + 1, min(height, int(round(y + crop_height))))

    crop = image[y1:y2, x1:x2]
    return crop if crop.size > 0 else image


def save_feedback_sample(base_dir, label, file_bytes, bbox=None, filename=None, timestamp=None):

    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported label: {label}")

    image = decode_image_bytes(file_bytes)
    bbox_dict = parse_bbox(bbox)
    cropped_image = crop_from_bbox(image, bbox_dict)

    timestamp_value = timestamp or datetime.utcnow().isoformat()
    safe_timestamp = timestamp_value.replace(":", "-").replace(".", "-")

    feedback_dir = Path(base_dir) / "data" / "feedback" / label
    feedback_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(filename or "feedback.png").stem
    output_path = feedback_dir / f"{safe_timestamp}_{original_name}.png"

    if not cv2.imwrite(str(output_path), cropped_image):
        raise ValueError("Failed to save feedback sample.")

    feedback_log = Path(base_dir) / "logs" / "feedback.jsonl"
    feedback_log.parent.mkdir(parents=True, exist_ok=True)

    with feedback_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "timestamp": timestamp_value,
            "label": label,
            "source_filename": filename,
            "saved_path": str(output_path.relative_to(base_dir)),
            "bbox": bbox_dict
        }) + "\n")

    return output_path
