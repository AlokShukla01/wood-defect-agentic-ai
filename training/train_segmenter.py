import random
import sys
from pathlib import Path

import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, roc_auc_score
from torch.utils.data import DataLoader, WeightedRandomSampler

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.segmentation_dataset import SegmentationDataset, build_segmentation_samples
from models.unet import HybridResNet50ViTUNet


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(42)
random.seed(42)

data_root = ROOT_DIR / "data" / "wood"
model_path = ROOT_DIR / "models" / "segmenter.pth"
epochs = 60
batch_size = 4
use_pretrained_encoder = True


def dice_loss(logits, targets, eps=1e-6):
    probs = torch.sigmoid(logits)
    intersection = (probs * targets).sum(dim=(1, 2, 3))
    union = probs.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
    dice = (2 * intersection + eps) / (union + eps)
    return 1 - dice.mean()


def focal_loss(logits, targets, alpha=0.75, gamma=2.0):
    bce = nn.functional.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    probs = torch.sigmoid(logits)
    pt = probs * targets + (1 - probs) * (1 - targets)
    loss = alpha * (1 - pt).pow(gamma) * bce
    return loss.mean()


def combined_loss(logits, targets):
    bce = nn.functional.binary_cross_entropy_with_logits(logits, targets)
    dice = dice_loss(logits, targets)
    focal = focal_loss(logits, targets)
    return bce + dice + 0.5 * focal


def evaluate(model, loader):
    model.eval()
    total_loss = 0.0
    total_iou = 0.0
    total_dice = 0.0
    total_items = 0
    auc_scores = []
    auc_targets = []

    with torch.no_grad():
        for images, masks in loader:
            images = images.to(device)
            masks = masks.to(device)
            logits = model(images)
            total_loss += combined_loss(logits, masks).item() * images.size(0)
            probs = torch.sigmoid(logits)
            preds = probs > 0.5
            targets = masks > 0.5

            intersection = (preds & targets).sum(dim=(1, 2, 3)).float()
            union = (preds | targets).sum(dim=(1, 2, 3)).float()
            pred_area = preds.sum(dim=(1, 2, 3)).float()
            target_area = targets.sum(dim=(1, 2, 3)).float()

            batch_iou = (intersection + 1e-6) / (union + 1e-6)
            batch_dice = (2 * intersection + 1e-6) / (pred_area + target_area + 1e-6)
            total_iou += batch_iou.sum().item()
            total_dice += batch_dice.sum().item()
            total_items += images.size(0)
            auc_scores.extend(probs.detach().cpu().reshape(-1).tolist())
            auc_targets.extend(targets.detach().cpu().reshape(-1).int().tolist())

    pixel_auc = 0.0
    pixel_ap = 0.0
    if len(set(auc_targets)) > 1:
        pixel_auc = roc_auc_score(auc_targets, auc_scores)
        pixel_ap = average_precision_score(auc_targets, auc_scores)

    return {
        "loss": total_loss / max(1, len(loader.dataset)),
        "iou": total_iou / max(1, total_items),
        "dice": total_dice / max(1, total_items),
        "pixel_auc": pixel_auc,
        "pixel_ap": pixel_ap,
    }


def build_weighted_sampler(samples):

    class_counts = {}
    for image_path, _ in samples:
        class_name = image_path.parent.name
        class_counts[class_name] = class_counts.get(class_name, 0) + 1

    sample_weights = [
        1.0 / class_counts[image_path.parent.name]
        for image_path, _ in samples
    ]

    return WeightedRandomSampler(
        weights=torch.DoubleTensor(sample_weights),
        num_samples=len(sample_weights),
        replacement=True,
    )


samples = build_segmentation_samples(data_root)
if len(samples) < 4:
    raise RuntimeError("Not enough segmentation samples to train the U-Net evaluator.")

val_size = max(1, int(0.2 * len(samples)))
train_size = len(samples) - val_size
random.Random(42).shuffle(samples)
train_samples = samples[:train_size]
val_samples = samples[train_size:]

train_dataset = SegmentationDataset(train_samples, augment=True)
val_dataset = SegmentationDataset(val_samples, augment=False)
train_sampler = build_weighted_sampler(train_samples)

train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=train_sampler)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

model = HybridResNet50ViTUNet(pretrained_encoder=use_pretrained_encoder).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="min",
    factor=0.5,
    patience=3,
)

best_val_auc = -1.0

print("Segmentation train samples:", len(train_dataset), flush=True)
print("Segmentation val samples:", len(val_dataset), flush=True)
print(f"Pretrained ResNet50 encoder requested: {use_pretrained_encoder}", flush=True)

for epoch in range(epochs):
    model.train()
    total_train_loss = 0.0

    for images, masks in train_loader:
        images = images.to(device)
        masks = masks.to(device)

        logits = model(images)
        loss = combined_loss(logits, masks)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_train_loss += loss.item() * images.size(0)

    train_loss = total_train_loss / max(1, len(train_loader.dataset))
    val_metrics = evaluate(model, val_loader)
    val_loss = val_metrics["loss"]
    scheduler.step(val_loss)

    print(
        f"Epoch {epoch + 1}/{epochs} "
        f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
        f"val_iou={val_metrics['iou']:.4f} val_dice={val_metrics['dice']:.4f} "
        f"val_auc={val_metrics['pixel_auc']:.4f} val_ap={val_metrics['pixel_ap']:.4f}"
    , flush=True)

    if val_metrics["pixel_auc"] >= best_val_auc:
        best_val_auc = val_metrics["pixel_auc"]
        torch.save(model.state_dict(), model_path)

print(f"Best segmentation val AUROC: {best_val_auc:.4f}", flush=True)
print(f"Saved segmenter to {model_path}", flush=True)
