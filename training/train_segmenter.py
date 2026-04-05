import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

from core.segmentation_dataset import SegmentationDataset, build_segmentation_samples
from models.unet import UNet


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(42)
random.seed(42)

data_root = Path("data/wood")
model_path = Path("models/segmenter.pth")
epochs = 20
batch_size = 4


def dice_loss(logits, targets, eps=1e-6):
    probs = torch.sigmoid(logits)
    intersection = (probs * targets).sum(dim=(1, 2, 3))
    union = probs.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
    dice = (2 * intersection + eps) / (union + eps)
    return 1 - dice.mean()


def combined_loss(logits, targets):
    bce = nn.functional.binary_cross_entropy_with_logits(logits, targets)
    dice = dice_loss(logits, targets)
    return bce + dice


def evaluate(model, loader):
    model.eval()
    total_loss = 0.0

    with torch.no_grad():
        for images, masks in loader:
            images = images.to(device)
            masks = masks.to(device)
            logits = model(images)
            total_loss += combined_loss(logits, masks).item() * images.size(0)

    return total_loss / max(1, len(loader.dataset))


samples = build_segmentation_samples(data_root)
if len(samples) < 4:
    raise RuntimeError("Not enough segmentation samples to train the U-Net evaluator.")

dataset = SegmentationDataset(samples)
val_size = max(1, int(0.2 * len(dataset)))
train_size = len(dataset) - val_size
train_dataset, val_dataset = random_split(
    dataset,
    [train_size, val_size],
    generator=torch.Generator().manual_seed(42)
)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

model = UNet().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

best_val_loss = float("inf")

print("Segmentation train samples:", len(train_dataset))
print("Segmentation val samples:", len(val_dataset))

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
    val_loss = evaluate(model, val_loader)

    print(
        f"Epoch {epoch + 1}/{epochs} "
        f"train_loss={train_loss:.4f} val_loss={val_loss:.4f}"
    )

    if val_loss <= best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), model_path)

print(f"Best segmentation val loss: {best_val_loss:.4f}")
print(f"Saved segmenter to {model_path}")
