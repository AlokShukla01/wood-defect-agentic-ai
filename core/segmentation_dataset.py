from pathlib import Path
import random

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision import transforms


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class SegmentationDataset(Dataset):

    def __init__(self, samples, image_transform=None, augment=False):
        self.samples = samples
        self.augment = augment
        self.image_transform = image_transform or transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        image_path, mask_path = self.samples[idx]

        image = cv2.imread(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

        image = cv2.resize(image, (224, 224))
        mask = cv2.resize(mask, (224, 224), interpolation=cv2.INTER_NEAREST)

        if self.augment:
            image, mask = self.apply_augmentation(image, mask)

        image_tensor = self.image_transform(image)
        mask_tensor = torch.from_numpy((mask > 0).astype("float32")).unsqueeze(0)

        return image_tensor, mask_tensor

    def apply_augmentation(self, image, mask):

        if random.random() < 0.5:
            image = cv2.flip(image, 1)
            mask = cv2.flip(mask, 1)

        if random.random() < 0.5:
            image = cv2.flip(image, 0)
            mask = cv2.flip(mask, 0)

        rotations = random.choice([0, 1, 2, 3])
        if rotations:
            image = np.rot90(image, rotations).copy()
            mask = np.rot90(mask, rotations).copy()

        if random.random() < 0.6:
            alpha = random.uniform(0.85, 1.15)
            beta = random.uniform(-12, 12)
            image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        if random.random() < 0.2:
            image = cv2.GaussianBlur(image, (3, 3), 0)

        return image, mask


def build_segmentation_samples(data_root):

    samples = []
    test_root = Path(data_root) / "test"
    gt_root = Path(data_root) / "ground_truth"

    for defect_dir in sorted(test_root.iterdir()):
        if not defect_dir.is_dir() or defect_dir.name == "good":
            continue

        gt_dir = gt_root / defect_dir.name
        if not gt_dir.exists():
            continue

        for image_path in sorted(defect_dir.glob("*")):
            if not image_path.is_file():
                continue

            mask_path = gt_dir / f"{image_path.stem}_mask.png"
            if mask_path.exists():
                samples.append((image_path, mask_path))

    return samples
