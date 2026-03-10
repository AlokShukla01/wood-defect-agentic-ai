import torch
import numpy as np
import joblib

from torch.utils.data import DataLoader

from core.dataset import WoodDataset
from core.feature_extractor import get_feature_extractor

from sklearn.ensemble import IsolationForest

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

dataset = WoodDataset("data/wood/train")

loader = DataLoader(dataset, batch_size=16)

model = get_feature_extractor()

features = []

with torch.no_grad():

    for imgs in loader:

        imgs = imgs.to(device)

        out = model(imgs)

        out = out.view(out.size(0), -1)

        features.append(out.cpu().numpy())

features = np.vstack(features)

iso = IsolationForest(contamination=0.01)

iso.fit(features)

joblib.dump(iso, "models/anomaly_model.pkl")

print("Anomaly model trained.")