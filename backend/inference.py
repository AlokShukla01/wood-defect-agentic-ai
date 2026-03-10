import torch
import joblib

from torchvision import models

from core.feature_extractor import get_feature_extractor

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# load anomaly model
anomaly_model = joblib.load("models/anomaly_model.pkl")

# load feature extractor
feature_model = get_feature_extractor()

# load classifier
classifier = models.resnet18(pretrained=False)
classifier.fc = torch.nn.Linear(classifier.fc.in_features, 5)

classifier.load_state_dict(torch.load("models/classifier.pth"))

classifier = classifier.to(device)
classifier.eval()

labels = ["color","combined","hole","liquid","scratch"]


def predict(img_tensor):

    img_tensor = img_tensor.to(device)

    # ---- CNN feature extraction ----
    with torch.no_grad():

        feat = feature_model(img_tensor)
        feat = feat.view(1,-1).cpu().numpy()

    # ---- anomaly detection ----
    anomaly = anomaly_model.predict(feat)

    if anomaly == 1:

        return {
            "status":"normal",
            "defect_type":None
        }

    # ---- defect classification ----
    with torch.no_grad():

        output = classifier(img_tensor)

        pred = torch.argmax(output,dim=1).item()

    return {
        "status":"defect",
        "defect_type":labels[pred]
    }