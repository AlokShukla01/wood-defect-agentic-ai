import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "logs" / "predictions.json"
CUTOFF = datetime.fromisoformat("2026-04-15T00:00:00")
OUTPUT_PATH = ROOT_DIR / "figures" / "iou_dice_by_defect_category.png"


def load_recent_best_metrics():
    best = defaultdict(lambda: {"iou": None, "dice": None})

    for line in LOG_PATH.read_text().splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue

        timestamp = row.get("timestamp")
        if not timestamp:
            continue

        normalized = timestamp if "T" in timestamp else timestamp.replace(" ", "T")
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            continue

        if dt < CUTOFF:
            continue

        defect = (row.get("prediction") or {}).get("defect_type")
        metrics = row.get("metrics") or {}
        if not defect or not metrics:
            continue

        iou = metrics.get("iou")
        dice = metrics.get("dice")

        if isinstance(iou, (int, float)):
            best[defect]["iou"] = iou if best[defect]["iou"] is None else max(best[defect]["iou"], iou)
        if isinstance(dice, (int, float)):
            best[defect]["dice"] = dice if best[defect]["dice"] is None else max(best[defect]["dice"], dice)

    ordered_defects = ["color", "combined", "hole", "liquid", "scratch"]
    values = {
        defect: best[defect]
        for defect in ordered_defects
        if best[defect]["iou"] is not None and best[defect]["dice"] is not None
    }
    return values


def main() -> None:
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    best = load_recent_best_metrics()

    defects = list(best.keys())
    best_iou = [best[d]["iou"] * 100 for d in defects]
    best_dice = [best[d]["dice"] * 100 for d in defects]

    x = np.arange(len(defects))
    width = 0.34

    plt.figure(figsize=(10, 5.8))
    bars_iou = plt.bar(
        x - width / 2,
        best_iou,
        width,
        label="IoU (%)",
        color="#d9d9d9",
        edgecolor="black",
        linewidth=1.0,
    )
    bars_dice = plt.bar(
        x + width / 2,
        best_dice,
        width,
        label="Dice (%)",
        color="#7f7f7f",
        edgecolor="black",
        linewidth=1.0,
    )

    plt.xticks(x, [d.title() for d in defects])
    plt.ylim(0, 100)
    plt.ylabel("Score (%)")
    plt.title("IoU and Dice by Defect Category")
    plt.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6, color="black")
    plt.legend(frameon=True, edgecolor="black", facecolor="white")

    for bars in (bars_iou, bars_dice):
        for bar in bars:
            value = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                value + 1.2,
                f"{value:.2f}%",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
