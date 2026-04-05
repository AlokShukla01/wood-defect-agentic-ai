import torch
import joblib
from torch.utils.data import DataLoader
from core.dataset import WoodDataset
from models.patchcore import PatchCore

dataset = WoodDataset("data/wood/train", label_map=None)
loader = DataLoader(dataset, batch_size=8, shuffle=False)

model = PatchCore()

model.build_memory(loader)

joblib.dump(model.memory, "models/patchcore_memory.pkl")

print("PatchCore trained")