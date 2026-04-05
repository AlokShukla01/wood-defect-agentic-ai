import cv2
import numpy as np


# -----------------------------
# Convert Heatmap to Binary Mask
# -----------------------------
def heatmap_to_mask(heatmap, threshold=0.5):

    # normalize
    heatmap = heatmap - heatmap.min()
    heatmap = heatmap / (heatmap.max() + 1e-8)

    # threshold
    mask = (heatmap > threshold).astype(np.uint8)

    return mask


# -----------------------------
# IoU
# -----------------------------
def compute_iou(pred_mask, gt_mask):

    pred = pred_mask > 0
    gt = gt_mask > 0

    intersection = np.logical_and(pred, gt).sum()
    union = np.logical_or(pred, gt).sum()

    if union == 0:
        return 1.0

    return intersection / union


# -----------------------------
# Dice Coefficient
# -----------------------------
def compute_dice(pred_mask, gt_mask):

    pred = pred_mask > 0
    gt = gt_mask > 0

    intersection = np.logical_and(pred, gt).sum()

    total = pred.sum() + gt.sum()

    if total == 0:
        return 1.0

    return (2 * intersection) / total


# -----------------------------
# Pixel Accuracy
# -----------------------------
def compute_accuracy(pred_mask, gt_mask):

    pred = pred_mask > 0
    gt = gt_mask > 0

    correct = (pred == gt).sum()
    total = pred.size

    return correct / total


# -----------------------------
# Full Evaluation Pipeline
# -----------------------------
def evaluate_prediction(heatmap, gt_mask):

    # resize GT to match heatmap
    gt_mask = cv2.resize(gt_mask, (heatmap.shape[1], heatmap.shape[0]))

    pred_mask = heatmap_to_mask(heatmap)

    iou = compute_iou(pred_mask, gt_mask)
    dice = compute_dice(pred_mask, gt_mask)
    acc = compute_accuracy(pred_mask, gt_mask)

    return {
        "iou": float(iou),
        "dice": float(dice),
        "accuracy": float(acc)
    }