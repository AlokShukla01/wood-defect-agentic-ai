import torch
import torch.nn as nn
import torch.optim as optim

from torchvision import models
from torch.utils.data import DataLoader

from core.dataset import WoodDataset

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

label_map = {
"color":0,
"combined":1,
"hole":2,
"liquid":3,
"scratch":4
}

dataset = WoodDataset("data/wood/test", label_map)

loader = DataLoader(dataset, batch_size=16, shuffle=True)

model = models.resnet18(pretrained=True)


for param in model.parameters():
    param.requires_grad = False


model.fc = nn.Linear(model.fc.in_features, 5)

model = model.to(device)

criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(model.fc.parameters(), lr=0.001)

for epoch in range(30):

    total_loss = 0

    for imgs, labels in loader:

        imgs, labels = imgs.to(device), labels.to(device)

        outputs = model(imgs)

        loss = criterion(outputs, labels)

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    print("Epoch:", epoch + 1, "Loss:", total_loss)

torch.save(model.state_dict(), "models/classifier.pth")

print("Classifier trained.")