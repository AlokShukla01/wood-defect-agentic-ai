import joblib
from torch.utils.data import DataLoader
from core.dataset import WoodDataset
from models.padim import PaDiM

dataset = WoodDataset("data/wood/train")
loader = DataLoader(dataset, batch_size=8)

model = PaDiM()
model.build_model(loader)

joblib.dump({
    "mean": model.mean,
    "cov_inv": model.cov_inv,
    "score_threshold": model.score_threshold,
    "feature_dim": model.feature_dim,
    "feature_hw": model.feature_hw
}, "models/padim.pkl")

print("✅ Saved PaDiM")
