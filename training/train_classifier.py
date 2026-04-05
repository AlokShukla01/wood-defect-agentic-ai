import random
from collections import Counter
from pathlib import Path

import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(42)
random.seed(42)

label_map = {
    "color": 0,
    "combined": 1,
    "hole": 2,
    "liquid": 3,
    "scratch": 4
}

dataset_roots = [
    Path("data/wood/test"),
    Path("data/feedback")
]
model_path = Path("models/classifier.pth")
num_epochs = 20
batch_size = 16
val_ratio = 0.2

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

train_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
])

eval_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
])


class DefectDataset(Dataset):

    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        image_path, label = self.samples[idx]
        image = cv2.imread(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = self.transform(image)
        return image, label


def build_samples():

    train_samples = []
    val_samples = []

    for class_name, label in label_map.items():
        images = []

        for root in dataset_roots:
            class_dir = root / class_name
            if class_dir.exists():
                images.extend(sorted(path for path in class_dir.glob("*") if path.is_file()))

        if not images:
            continue

        random.shuffle(images)
        split_idx = max(1, int(len(images) * (1 - val_ratio)))

        if split_idx >= len(images):
            split_idx = len(images) - 1

        train_images = images[:split_idx]
        val_images = images[split_idx:]

        train_samples.extend((image_path, label) for image_path in train_images)
        val_samples.extend((image_path, label) for image_path in val_images)

    return train_samples, val_samples


def evaluate(model, loader):

    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_items = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)
            total_correct += (outputs.argmax(dim=1) == labels).sum().item()
            total_items += images.size(0)

    return total_loss / total_items, total_correct / total_items


train_samples, val_samples = build_samples()

if not train_samples or not val_samples:
    raise RuntimeError("Not enough labeled defect images to create train/validation splits.")

print("Training samples:", len(train_samples), flush=True)
print("Validation samples:", len(val_samples), flush=True)
print("Train class counts:", dict(Counter(label for _, label in train_samples)), flush=True)
print("Val class counts:", dict(Counter(label for _, label in val_samples)), flush=True)

train_dataset = DefectDataset(train_samples, train_transform)
val_dataset = DefectDataset(val_samples, eval_transform)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

for param in model.parameters():
    param.requires_grad = False

for param in model.layer4.parameters():
    param.requires_grad = True

model.fc = nn.Linear(model.fc.in_features, len(label_map))
model = model.to(device)

class_counts = Counter(label for _, label in train_samples)
class_weights = []

for label in range(len(label_map)):
    class_weights.append(len(train_samples) / (len(label_map) * class_counts[label]))

criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights, dtype=torch.float32, device=device))
optimizer = optim.Adam([
    {"params": model.layer4.parameters(), "lr": 1e-4},
    {"params": model.fc.parameters(), "lr": 1e-3}
], weight_decay=1e-4)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.3)

best_val_acc = 0.0

for epoch in range(num_epochs):

    model.train()
    total_loss = 0.0
    total_correct = 0
    total_items = 0

    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        total_correct += (outputs.argmax(dim=1) == labels).sum().item()
        total_items += images.size(0)

    scheduler.step()

    train_loss = total_loss / total_items
    train_acc = total_correct / total_items
    val_loss, val_acc = evaluate(model, val_loader)

    print(
        f"Epoch {epoch + 1}/{num_epochs} "
        f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
        f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
    , flush=True)

    if val_acc >= best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), model_path)

print(f"Best validation accuracy: {best_val_acc:.4f}", flush=True)
print(f"Saved classifier to {model_path}", flush=True)
