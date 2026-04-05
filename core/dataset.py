import os
import cv2
from torch.utils.data import Dataset
from torchvision import transforms


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class WoodDataset(Dataset):

    def __init__(self, root, label_map=None, transform=None):

        self.images = []
        self.labels = []
        self.label_map = label_map

        for folder in os.listdir(root):

            folder_path = os.path.join(root, folder)

            if os.path.isdir(folder_path):

                 if label_map and folder not in label_map:
                    continue

                 for img in os.listdir(folder_path):

                    self.images.append(os.path.join(folder_path, img))

                    if label_map:
                        self.labels.append(label_map[folder])

        self.transform = transform or transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):

        img = cv2.imread(self.images[idx])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img = self.transform(img)

        if self.label_map:
            return img, self.labels[idx]

        return img
