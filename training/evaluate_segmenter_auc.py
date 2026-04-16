import sys
from pathlib import Path

import cv2
import joblib
import numpy as np
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.segmentation_dataset import IMAGENET_MEAN, IMAGENET_STD, build_segmentation_samples
from models.padim import PaDiM
from models.unet import HybridResNet50ViTUNet, UNet


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
data_root = ROOT_DIR / "data" / "wood"
model_path = ROOT_DIR / "models" / "segmenter.pth"
padim_path = ROOT_DIR / "models" / "padim.pkl"


def load_segmenter():

    state_dict = torch.load(model_path, map_location=device)
    model = HybridResNet50ViTUNet(pretrained_encoder=False).to(device)
    model_name = "hybrid_resnet50_vit_segmenter"

    try:
        model.load_state_dict(state_dict)
    except RuntimeError:
        model = UNet().to(device)
        model.load_state_dict(state_dict)
        model_name = "legacy_unet_segmenter"

    model.eval()
    return model, model_name


def image_to_tensor(image):

    image = cv2.resize(image, (224, 224))
    image = image.astype(np.float32) / 255.0
    image = (image - np.array(IMAGENET_MEAN, dtype=np.float32)) / np.array(
        IMAGENET_STD, dtype=np.float32
    )
    image = image.transpose(2, 0, 1)
    return torch.from_numpy(image).unsqueeze(0).float()


def load_padim():

    if not padim_path.exists():
        return None

    model = PaDiM()
    payload = joblib.load(padim_path)
    model.mean = payload["mean"]
    model.cov_inv = payload["cov_inv"]
    model.score_threshold = payload.get("score_threshold")
    model.feature_dim = payload.get("feature_dim")
    model.feature_hw = tuple(payload["feature_hw"]) if payload.get("feature_hw") is not None else tuple(model.mean.shape[:2])
    return model


def normalized_padim_map(padim, tensor, output_shape):

    if padim is None:
        return None

    feat = padim.extract(tensor)
    dist_map = padim.distance_map_from_features(feat)[0]
    dist_map = cv2.resize(dist_map, output_shape)
    return (dist_map - dist_map.min()) / (dist_map.max() - dist_map.min() + 1e-8)


def metric_pair(targets, scores):

    if len(set(targets)) < 2:
        return None, None

    return roc_auc_score(targets, scores), average_precision_score(targets, scores)


def main():

    samples = build_segmentation_samples(data_root)
    if not samples:
        raise RuntimeError("No segmentation samples found.")

    model, model_name = load_segmenter()
    padim = load_padim()
    all_scores = []
    all_padim_scores = []
    all_targets = []
    per_class = {}
    fusion_weights = [0.5, 0.6, 0.7, 0.8]
    fusion_scores = {weight: [] for weight in fusion_weights}

    with torch.no_grad():
        for image_path, mask_path in samples:
            image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

            tensor = image_to_tensor(image).to(device)
            logits = model(tensor)
            probs = torch.sigmoid(logits)[0, 0].cpu().numpy()
            probs = cv2.resize(probs, (224, 224))
            padim_map = normalized_padim_map(padim, tensor, (224, 224))

            mask = cv2.resize(mask, (224, 224), interpolation=cv2.INTER_NEAREST)
            target = (mask > 0).astype(np.uint8)

            all_scores.extend(probs.reshape(-1).tolist())
            all_targets.extend(target.reshape(-1).tolist())

            if padim_map is not None:
                all_padim_scores.extend(padim_map.reshape(-1).tolist())
                for weight in fusion_weights:
                    fused = weight * probs + (1 - weight) * padim_map
                    fusion_scores[weight].extend(fused.reshape(-1).tolist())

            class_name = image_path.parent.name
            bucket = per_class.setdefault(class_name, {"scores": [], "targets": [], "count": 0})
            bucket["scores"].extend(probs.reshape(-1).tolist())
            bucket["targets"].extend(target.reshape(-1).tolist())
            bucket["count"] += 1

    overall_auc, overall_ap = metric_pair(all_targets, all_scores)

    print(f"Model: {model_name}")
    print(f"Samples: {len(samples)}")
    print(f"Pixel AUROC: {overall_auc:.4f}")
    print(f"Pixel AP: {overall_ap:.4f}")

    if all_padim_scores:
        padim_auc, padim_ap = metric_pair(all_targets, all_padim_scores)
        print(f"PaDiM Pixel AUROC: {padim_auc:.4f}")
        print(f"PaDiM Pixel AP: {padim_ap:.4f}")

        best_fusion = None
        for weight, scores in fusion_scores.items():
            fusion_auc, fusion_ap = metric_pair(all_targets, scores)
            print(
                f"Fusion w={weight:.1f} segmenter + {1 - weight:.1f} PaDiM: "
                f"pixel_auroc={fusion_auc:.4f} pixel_ap={fusion_ap:.4f}"
            )
            if best_fusion is None or fusion_auc > best_fusion[1]:
                best_fusion = (weight, fusion_auc, fusion_ap)

        if best_fusion:
            print(
                f"Best Fusion: w={best_fusion[0]:.1f}, "
                f"pixel_auroc={best_fusion[1]:.4f}, pixel_ap={best_fusion[2]:.4f}"
            )

    print()
    print("Class-wise pixel AUROC/AP:")

    for class_name in sorted(per_class):
        values = per_class[class_name]
        targets = values["targets"]
        scores = values["scores"]

        if len(set(targets)) < 2:
            continue

        auc = roc_auc_score(targets, scores)
        ap = average_precision_score(targets, scores)
        print(
            f"{class_name}: count={values['count']} "
            f"pixel_auroc={auc:.4f} pixel_ap={ap:.4f}"
        )


if __name__ == "__main__":
    main()
