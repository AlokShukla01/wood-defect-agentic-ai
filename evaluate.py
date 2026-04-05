import os
import cv2
import torch
import joblib
import numpy as np

from torchvision import models, transforms
from core.feature_extractor import get_feature_extractor


# ----------------------------
# Device
# ----------------------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ----------------------------
# Load Models
# ----------------------------

anomaly_model = joblib.load("models/anomaly_model.pkl")

feature_model = get_feature_extractor()

classifier = models.resnet18(pretrained=False)
classifier.fc = torch.nn.Linear(classifier.fc.in_features,5)

classifier.load_state_dict(torch.load("models/classifier.pth"))

classifier = classifier.to(device)
classifier.eval()

labels = ["color","combined","hole","liquid","scratch"]


# ----------------------------
# Image Transform
# ----------------------------

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224,224)),
    transforms.ToTensor()
])


# ----------------------------
# Dataset Path
# ----------------------------

test_path = "data/wood/test"


# ----------------------------
# Counters
# ----------------------------

TP = 0
TN = 0
FP = 0
FN = 0

y_true = []
y_pred = []


# ----------------------------
# Loop Through Test Images
# ----------------------------

for defect in os.listdir(test_path):

    folder = os.path.join(test_path,defect)

    for img_name in os.listdir(folder):

        img_path = os.path.join(folder,img_name)

        img = cv2.imread(img_path)
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

        img_tensor = transform(img).unsqueeze(0).to(device)


        # --------------------
        # Feature Extraction
        # --------------------

        with torch.no_grad():

            feat = feature_model(img_tensor)
            feat = feat.view(1,-1).cpu().numpy()


        # --------------------
        # Anomaly Detection
        # --------------------

        anomaly = anomaly_model.predict(feat)[0]


        # --------------------
        # Classification
        # --------------------

        if anomaly == -1:

            with torch.no_grad():

                output = classifier(img_tensor)
                pred = torch.argmax(output,dim=1).item()

            pred_label = labels[pred]

        else:

            pred_label = "good"


        # --------------------
        # Store labels
        # --------------------

        y_true.append(defect)
        y_pred.append(pred_label)


        # --------------------
        # Confusion counts
        # --------------------

        if defect == "good" and pred_label == "good":
            TN += 1

        elif defect != "good" and pred_label != "good":
            TP += 1

        elif defect == "good" and pred_label != "good":
            FP += 1

        else:
            FN += 1


# ----------------------------
# Metrics
# ----------------------------

accuracy = (TP + TN) / (TP + TN + FP + FN + 1e-8)

precision = TP / (TP + FP + 1e-8)

recall = TP / (TP + FN + 1e-8)

f1 = 2 * (precision * recall) / (precision + recall + 1e-8)


# ----------------------------
# Confusion Matrix
# ----------------------------

print("\nConfusion Matrix")
print("-------------------")
print("TP:",TP)
print("TN:",TN)
print("FP:",FP)
print("FN:",FN)


print("\nEvaluation Metrics")
print("-------------------")

print("Accuracy :",round(accuracy,4))
print("Precision:",round(precision,4))
print("Recall   :",round(recall,4))
print("F1 Score :",round(f1,4))