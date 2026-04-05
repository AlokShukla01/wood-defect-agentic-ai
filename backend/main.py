import json
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

from backend.agent import build_agent_review
from backend.feedback import ALLOWED_LABELS, save_feedback_sample
from backend.inference import predict, reload_classifier
from backend.logging_utils import append_prediction_log
from backend.retrain import get_retrain_status, is_retraining, start_retraining_job
from utils.image_utils import load_image

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict")
async def predict_image(
    file: UploadFile = File(...),
    dataset_label: str | None = Form(None),
):

    contents = await file.read()
    print("📁 Uploaded filename:", file.filename) 
    img_tensor = load_image(contents)

    np_arr = np.frombuffer(contents, np.uint8)
    img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # 🔥 pass filename
    result = predict(img_tensor, img_np, file.filename, dataset_label=dataset_label)
    append_prediction_log(BASE_DIR, result, file.filename)

    return result


@app.post("/feedback")
async def store_feedback(
    file: UploadFile = File(...),
    label: str = Form(...),
    bbox: str | None = Form(None),
    timestamp: str | None = Form(None),
):

    if label not in ALLOWED_LABELS:
        raise HTTPException(status_code=400, detail="Unsupported label")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    try:
        saved_path = save_feedback_sample(
            base_dir=BASE_DIR,
            label=label,
            file_bytes=file_bytes,
            bbox=bbox,
            filename=file.filename,
            timestamp=timestamp
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid bbox payload")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "feedback_saved",
        "label": label,
        "saved_path": str(saved_path.relative_to(BASE_DIR)),
        "retraining_started": False,
        "message": "Feedback stored. Use the retraining button when you are ready to update the classifier."
    }


@app.get("/agent/review")
async def review_agent_state(limit: int = 100, trigger_retraining: bool = False):

    review = build_agent_review(BASE_DIR, limit=limit)

    retraining_started = False

    if trigger_retraining and review["recommendation"] == "start_retraining" and not is_retraining():
        retraining_started = start_retraining_job(BASE_DIR, reload_classifier)

    review["retraining_started"] = retraining_started

    if trigger_retraining and not retraining_started:
        review["retraining_message"] = "Retraining was not started."
    elif retraining_started:
        review["retraining_message"] = "Agent review started classifier retraining."

    return review


@app.get("/retrain/status")
async def retrain_status():

    return get_retrain_status()
