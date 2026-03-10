import cv2
import numpy as np
from torchvision import transforms

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224,224)),
    transforms.ToTensor()
])

def load_image(file_bytes):

    nparr = np.frombuffer(file_bytes,np.uint8)

    img = cv2.imdecode(nparr,cv2.IMREAD_COLOR)

    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

    img = transform(img)

    return img.unsqueeze(0)