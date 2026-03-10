import torch
import torchvision.models as models

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_feature_extractor():

    model = models.resnet18(pretrained=True)

    model = torch.nn.Sequential(*list(model.children())[:-1])

    model = model.to(device)

    model.eval()

    return model