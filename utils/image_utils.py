import cv2
import numpy as np
from torchvision import transforms

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
])

def load_image(file_bytes):

    nparr = np.frombuffer(file_bytes,np.uint8)

    img = cv2.imdecode(nparr,cv2.IMREAD_COLOR)

    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

    img = transform(img)

    return img.unsqueeze(0)
