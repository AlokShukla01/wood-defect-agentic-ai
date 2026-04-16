import torch
import joblib
import cv2
import numpy as np
import base64
import glob
import os

from torchvision import models
from backend.agent import build_agent_plan
from backend.evaluation import evaluate_prediction
from models.padim import PaDiM
from models.unet import HybridResNet50ViTUNet, UNet

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LOW_CONFIDENCE_THRESHOLD = 0.70
SEGMENTER_PROB_THRESHOLD = 0.75
SEGMENTER_MIN_COMPONENT_AREA_RATIO = 0.0005
ANOMALY_SUPPORT_THRESHOLD = 0.35

# -----------------------------
# BASE DIR
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

classifier = None
segmenter = None
segmenter_model_name = None
runtime_anomaly_threshold = None

# -----------------------------
# Load PaDiM (🔥 IMPORTANT)
# -----------------------------
padim = PaDiM()

padim_data = joblib.load(os.path.join(BASE_DIR, "models/padim.pkl"))
padim.mean = padim_data["mean"]
padim.cov_inv = padim_data["cov_inv"]
padim.score_threshold = padim_data.get("score_threshold")
padim.feature_dim = padim_data.get("feature_dim")
padim.feature_hw = tuple(padim_data["feature_hw"]) if padim_data.get("feature_hw") is not None else tuple(padim.mean.shape[:2])

labels = ["color","combined","hole","liquid","scratch"]


def _image_to_tensor(image_path):

    from utils.image_utils import load_image

    with open(image_path, "rb") as handle:
        return load_image(handle.read())


def estimate_runtime_anomaly_threshold(max_good_samples=80):

    good_dir = os.path.join(BASE_DIR, "data", "wood", "train", "good")
    if not os.path.isdir(good_dir):
        return padim.score_threshold

    image_paths = sorted(
        path for path in glob.glob(os.path.join(good_dir, "*"))
        if os.path.isfile(path)
    )[:max_good_samples]

    if not image_paths:
        return padim.score_threshold

    scores = []

    for image_path in image_paths:
        try:
            tensor = _image_to_tensor(image_path).to(device)
            feat = padim.extract(tensor)
            dist_map = padim.distance_map_from_features(feat)
            scores.append(float(padim.image_scores(dist_map)[0]))
        except Exception:
            continue

    if not scores:
        return padim.score_threshold

    percentile_threshold = float(np.percentile(scores, 99))
    conservative_floor = float(np.mean(scores) + 4.0 * np.std(scores))
    return max(percentile_threshold, conservative_floor, float(padim.score_threshold or 0.0))


runtime_anomaly_threshold = estimate_runtime_anomaly_threshold()
print(f"✅ Runtime anomaly threshold: {runtime_anomaly_threshold:.3f}")

# -----------------------------
# Grad-CAM Setup
# -----------------------------
gradients = []
activations = []


def calibrate_prediction_confidence(
    raw_confidence,
    is_defect,
    anomaly_score=None,
    anomaly_threshold=None,
    metrics=None,
):

    raw_confidence = float(raw_confidence)
    anomaly_factor = 1.0
    quality_factor = 1.0

    if anomaly_score is not None and anomaly_threshold not in (None, 0):
        if is_defect:
            anomaly_factor = min(1.0, max(0.60, anomaly_score / (anomaly_threshold * 1.5)))
        else:
            anomaly_factor = min(1.0, max(0.60, (anomaly_threshold - anomaly_score) / anomaly_threshold))

    if metrics is not None:
        iou = float(metrics.get("iou", 0.0))
        if iou < 0.25:
            quality_factor = 0.62
        elif iou < 0.45:
            quality_factor = 0.78
        elif iou < 0.60:
            quality_factor = 0.88
        else:
            quality_factor = 0.95

    confidence = (
        (0.75 * raw_confidence) +
        (0.15 * anomaly_factor) +
        (0.10 * quality_factor)
    )

    return max(0.10, min(0.99, confidence))


def is_probable_defect(anomaly_score, raw_confidence):

    if anomaly_score is None:
        return raw_confidence >= 0.80

    threshold = runtime_anomaly_threshold or padim.score_threshold

    if threshold is None:
        return raw_confidence >= 0.80

    if anomaly_score >= threshold:
        return True

    borderline_threshold = 0.75 * threshold
    return raw_confidence >= 0.88 and anomaly_score >= borderline_threshold


def load_classifier():

    global classifier

    loaded_classifier = models.resnet18(weights=None)
    loaded_classifier.fc = torch.nn.Linear(loaded_classifier.fc.in_features, 5)
    loaded_classifier.load_state_dict(
        torch.load(os.path.join(BASE_DIR, "models/classifier.pth"), map_location=device)
    )
    loaded_classifier = loaded_classifier.to(device)
    loaded_classifier.eval()

    loaded_classifier.layer4.register_forward_hook(save_activation)
    loaded_classifier.layer4.register_full_backward_hook(save_gradient)

    classifier = loaded_classifier
    print("✅ Classifier loaded")


def reload_classifier():

    gradients.clear()
    activations.clear()
    load_classifier()


def load_segmenter():

    global segmenter, segmenter_model_name

    segmenter_path = os.path.join(BASE_DIR, "models/segmenter.pth")
    if not os.path.exists(segmenter_path):
        segmenter = None
        segmenter_model_name = None
        print("⚠️ Segmenter model not found. Falling back to PaDiM masks for evaluation.")
        return

    state_dict = torch.load(segmenter_path, map_location=device)
    loaded_segmenter = HybridResNet50ViTUNet(pretrained_encoder=False).to(device)

    try:
        loaded_segmenter.load_state_dict(state_dict)
        segmenter_model_name = "hybrid_resnet50_vit_segmenter"
    except RuntimeError:
        print("⚠️ Hybrid segmenter weights not found. Loading legacy U-Net segmenter.")
        loaded_segmenter = UNet().to(device)
        loaded_segmenter.load_state_dict(state_dict)
        segmenter_model_name = "unet_segmenter_refined"

    loaded_segmenter.eval()
    segmenter = loaded_segmenter
    print("✅ Segmenter loaded")

def save_gradient(module, grad_input, grad_output):
    gradients.append(grad_output[0])

def save_activation(module, input, output):
    activations.append(output)

# -----------------------------
# Grad-CAM
# -----------------------------
def generate_cam_map(img_tensor, img_np):

    gradients.clear()
    activations.clear()

    img_tensor = img_tensor.clone().detach().requires_grad_(True)

    output = classifier(img_tensor)
    pred_class = torch.argmax(output, dim=1)

    classifier.zero_grad()
    output[0, pred_class].backward()

    grad = gradients[-1]
    act = activations[-1]

    weights = torch.mean(grad, dim=(2,3), keepdim=True)
    cam = torch.sum(weights * act, dim=1).squeeze()

    cam = torch.relu(cam).detach().cpu().numpy()

    cam = cv2.resize(cam, (img_np.shape[1], img_np.shape[0]))
    cam = (cam - cam.min()) / (cam.max() + 1e-8)

    return cam


def generate_heatmap(img_tensor, img_np):

    cam = generate_cam_map(img_tensor, img_np)

    heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img_np, 0.6, heatmap, 0.4, 0)

    _, buffer = cv2.imencode('.png', overlay)
    return base64.b64encode(buffer).decode('utf-8')


def encode_mask(mask):

    mask_img = (mask > 0).astype(np.uint8) * 255
    mask_img = cv2.cvtColor(mask_img, cv2.COLOR_GRAY2BGR)
    _, buffer = cv2.imencode(".png", mask_img)
    return base64.b64encode(buffer).decode("utf-8")


def encode_comparison_overlay(pred_mask, gt_mask):

    pred = (pred_mask > 0)
    gt = (gt_mask > 0)

    overlay = np.zeros((pred_mask.shape[0], pred_mask.shape[1], 3), dtype=np.uint8)

    true_positive = pred & gt
    false_positive = pred & (~gt)
    false_negative = (~pred) & gt

    overlay[true_positive] = (0, 200, 0)
    overlay[false_positive] = (0, 165, 255)
    overlay[false_negative] = (255, 80, 80)

    _, buffer = cv2.imencode(".png", overlay)

    return base64.b64encode(buffer).decode("utf-8"), {
        "true_positive_pixels": int(true_positive.sum()),
        "false_positive_pixels": int(false_positive.sum()),
        "false_negative_pixels": int(false_negative.sum()),
    }


def filter_mask_components(mask, support_map=None, min_area_ratio=SEGMENTER_MIN_COMPONENT_AREA_RATIO):

    mask = (mask > 0).astype(np.uint8)
    min_area = max(16, int(min_area_ratio * mask.shape[0] * mask.shape[1]))

    num_labels, cc_labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    filtered_mask = np.zeros_like(mask)

    for component_idx in range(1, num_labels):
        area = stats[component_idx, cv2.CC_STAT_AREA]

        if area < min_area:
            continue

        component = cc_labels == component_idx

        if support_map is not None:
            component_support = float(support_map[component].mean())
            if component_support < ANOMALY_SUPPORT_THRESHOLD:
                continue

        filtered_mask[component] = 1

    return filtered_mask


def segment_defect_mask(img_tensor, img_np, support_map=None):

    if segmenter is None:
        return None

    with torch.no_grad():
        logits = segmenter(img_tensor.to(device))
        probs = torch.sigmoid(logits)[0, 0].cpu().numpy()

    probs = cv2.resize(probs, (img_np.shape[1], img_np.shape[0]))
    probs = cv2.GaussianBlur(probs, (5, 5), 0)

    if segmenter_model_name == "hybrid_resnet50_vit_segmenter" and support_map is not None:
        support_resized = cv2.resize(support_map, (img_np.shape[1], img_np.shape[0]))
        support_resized = (support_resized - support_resized.min()) / (
            support_resized.max() - support_resized.min() + 1e-8
        )
        probs = 0.70 * probs + 0.30 * support_resized

    otsu_input = np.uint8(255 * np.clip(probs, 0, 1))
    otsu_threshold, _ = cv2.threshold(
        otsu_input, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    adaptive_threshold = float(otsu_threshold) / 255.0

    if segmenter_model_name == "hybrid_resnet50_vit_segmenter":
        threshold = float(np.clip(adaptive_threshold, 0.30, 0.65))
    else:
        threshold = SEGMENTER_PROB_THRESHOLD

    mask = (probs > threshold).astype(np.uint8)

    if mask.sum() == 0 and segmenter_model_name == "hybrid_resnet50_vit_segmenter":
        fallback_threshold = max(0.20, threshold - 0.15)
        mask = (probs > fallback_threshold).astype(np.uint8)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = filter_mask_components(mask, support_map=support_map)

    return mask


def resolve_ground_truth_path(
    filename,
    img_np=None,
    predicted_label=None,
    confidence=None,
    is_defect=None,
    dataset_label=None
):

    normalized_filename = (filename or "").replace("\\", "/")
    name = os.path.splitext(os.path.basename(normalized_filename))[0]
    parts = [part for part in normalized_filename.split("/") if part]
    defect_folder = parts[-2] if len(parts) > 1 else None

    if defect_folder not in labels and img_np is not None and name:
        candidate_pattern = os.path.join(BASE_DIR, "data", "wood", "test", "*", name + ".*")
        for candidate_path in sorted(glob.glob(candidate_pattern)):
            candidate_folder = os.path.basename(os.path.dirname(candidate_path))
            if candidate_folder not in labels:
                continue

            candidate_image = cv2.imread(candidate_path, cv2.IMREAD_COLOR)
            if candidate_image is None:
                continue

            if candidate_image.shape == img_np.shape and np.array_equal(candidate_image, img_np):
                defect_folder = candidate_folder
                break

    if dataset_label in labels:
        defect_folder = dataset_label
    elif defect_folder not in labels:
        if (
            predicted_label in labels
            and is_defect
            and confidence is not None
            and confidence >= LOW_CONFIDENCE_THRESHOLD
        ):
            defect_folder = predicted_label

    if defect_folder == "good":
        return None, defect_folder

    if defect_folder not in labels:
        return None, defect_folder

    return os.path.join(
        BASE_DIR,
        "data",
        "wood",
        "ground_truth",
        defect_folder,
        name + "_mask.png"
    ), defect_folder


# -----------------------------
# Predict
# -----------------------------
def predict(img_tensor, img_np, filename, dataset_label=None):

    img_tensor = img_tensor.to(device)

    print("\n📌 Filename:", filename)

    # -----------------------------
    # Classification
    # -----------------------------
    with torch.no_grad():
        output = classifier(img_tensor)
        probs = torch.softmax(output, dim=1)
        pred = torch.argmax(probs, dim=1).item()
        raw_confidence = probs[0][pred].item()

    metrics = None
    anomaly_score = None
    pred_mask = None
    cam_map = None
    predicted_mask_b64 = None
    actual_gt_mask_b64 = None
    comparison_overlay_b64 = None
    comparison_stats = None
    evaluation_model = "padim"
    matched_defect_folder = None

    if raw_confidence >= 0.5:
        try:
            cam_map = generate_cam_map(img_tensor, img_np)
        except Exception as e:
            print("⚠️ CAM generation failed:", e)
            cam_map = None

    try:
        feat = padim.extract(img_tensor)
        dist_map = padim.distance_map_from_features(feat)
        anomaly_score = float(padim.image_scores(dist_map)[0])
        anomaly_map = cv2.resize(dist_map[0], (img_np.shape[1], img_np.shape[0]))

        print("✅ PaDiM anomaly map generated")
        print("📈 Anomaly score:", anomaly_score)

        anomaly_map = (anomaly_map - anomaly_map.min()) / (anomaly_map.max() + 1e-8)

        if cam_map is not None:
            anomaly_map = 0.7 * anomaly_map + 0.3 * cam_map

        anomaly_map = cv2.GaussianBlur(anomaly_map, (5, 5), 0)

        otsu_input = np.uint8(255 * anomaly_map)
        _, pred_mask = cv2.threshold(
            otsu_input, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        open_kernel = np.ones((3, 3), np.uint8)
        close_kernel = np.ones((5, 5), np.uint8)
        pred_mask = cv2.morphologyEx(pred_mask, cv2.MORPH_OPEN, open_kernel)
        pred_mask = cv2.morphologyEx(pred_mask, cv2.MORPH_CLOSE, close_kernel)
        pred_mask = filter_mask_components(pred_mask, support_map=anomaly_map)

        is_defect = is_probable_defect(anomaly_score, raw_confidence)

        # -----------------------------
        # GT SEARCH
        # -----------------------------
        gt_path, matched_defect_folder = resolve_ground_truth_path(
            filename,
            img_np=img_np,
            predicted_label=labels[pred],
            confidence=raw_confidence,
            is_defect=is_defect,
            dataset_label=dataset_label
        )

        if gt_path and os.path.exists(gt_path):

            print("✅ GT FOUND:", gt_path)

            gt_mask = cv2.imread(gt_path, 0)

            if gt_mask is not None:

                gt_mask = cv2.resize(gt_mask, (pred_mask.shape[1], pred_mask.shape[0]))

                eval_mask = pred_mask
                segmenter_mask = segment_defect_mask(img_tensor, img_np, support_map=anomaly_map)

                if segmenter_mask is not None and segmenter_mask.sum() > 0:
                    eval_mask = segmenter_mask
                    evaluation_model = segmenter_model_name or "segmenter_refined"

                metrics = evaluate_prediction(eval_mask, gt_mask)
                predicted_mask_b64 = encode_mask(eval_mask)
                actual_gt_mask_b64 = encode_mask(gt_mask)
                comparison_overlay_b64, comparison_stats = encode_comparison_overlay(eval_mask, gt_mask)

                print("✅ Metrics:", metrics)
        elif gt_path:
            print("⚠️ GT PATH NOT FOUND:", gt_path)
        else:
            print("ℹ️ Ground truth comparison skipped because the upload path does not identify a dataset defect folder.")

        if metrics is None:
            print("⚠️ GT NOT FOUND OR FAILED")

    except Exception as e:
        print("❌ PaDiM ERROR:", e)
        metrics = None

    is_defect = is_probable_defect(anomaly_score, raw_confidence)

    confidence = calibrate_prediction_confidence(
        raw_confidence=raw_confidence,
        is_defect=is_defect,
        anomaly_score=anomaly_score,
        anomaly_threshold=runtime_anomaly_threshold or padim.score_threshold,
        metrics=metrics,
    )

    resolved_defect_type = labels[pred] if is_defect and confidence >= LOW_CONFIDENCE_THRESHOLD else None
    prediction_source = "classifier"

    if is_defect and confidence >= LOW_CONFIDENCE_THRESHOLD and matched_defect_folder in labels:
        resolved_defect_type = matched_defect_folder
        prediction_source = "dataset_match"

    result = {
        "status": "defect" if is_defect else "normal",
        "defect_type": resolved_defect_type
    }

    # -----------------------------
    # Heatmap (Grad-CAM)
    # -----------------------------
    heatmap = generate_heatmap(img_tensor, img_np)

    # -----------------------------
    # Agent Decision
    # -----------------------------
    agent_plan = build_agent_plan(
        prediction=result,
        confidence=confidence,
        anomaly_score=anomaly_score,
        anomaly_threshold=runtime_anomaly_threshold or padim.score_threshold,
        metrics=metrics,
        has_ground_truth=metrics is not None,
        evaluation_model=evaluation_model,
        base_dir=BASE_DIR,
        source_filename=filename,
    )
    agent_action = agent_plan["action"]

    default_user_message = {
        "request_user_label": (
            "Prediction confidence is low. Please review the image, provide the correct label, "
            "and submit feedback so the model can relearn from it."
        ),
        "predict_and_monitor": (
            "The model predicted a defect type, but there is no ground truth available for this upload. "
            "Please verify the result visually."
        ),
        "review_mask_quality": (
            "The defect type looks plausible, but the localized defect region should be monitored."
        ),
        "request_mask_feedback": (
            "The system detected a defect, but the highlighted region looks weak. "
            "Please refine the defect area and submit feedback."
        ),
    }
    user_message = default_user_message.get(agent_action)

    # -----------------------------
    # Response
    # -----------------------------
    return {
        "prediction": result,
        "classifier_predicted_label": labels[pred],
        "prediction_source": prediction_source,
        "confidence": confidence,
        "confidence_threshold": LOW_CONFIDENCE_THRESHOLD,
        "anomaly_score": anomaly_score,
        "anomaly_threshold": runtime_anomaly_threshold or padim.score_threshold,
        "heatmap": heatmap,
        "metrics": metrics,
        "predicted_mask": predicted_mask_b64,
        "actual_ground_truth_mask": actual_gt_mask_b64,
        "comparison_overlay": comparison_overlay_b64,
        "comparison_stats": comparison_stats,
        "evaluation_model": evaluation_model,
        "agent": agent_plan,
        "agent_action": agent_action,
        "requires_user_input": agent_action in {"request_user_label", "request_mask_feedback"},
        "user_message": user_message
    }


load_classifier()
load_segmenter()
