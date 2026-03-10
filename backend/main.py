from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.inference import predict
from utils.image_utils import load_image

app = FastAPI()

# allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict")
async def predict_image(file: UploadFile):

    contents = await file.read()

    img_tensor = load_image(contents)

    result = predict(img_tensor)

    return result