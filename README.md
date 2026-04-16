# Wood Defect Agentic AI

Wood defect inspection system built with:
- a CNN classifier for known defect classes
- PaDiM anomaly detection for defect vs normal analysis
- a custom hybrid ResNet50-ViT segmenter with attention skip connections for defect mask refinement
- a FastAPI backend
- a React + Vite frontend
- a local workflow-based agentic review and retraining loop

## What The Project Does

1. Accepts a wood surface image from the frontend.
2. Predicts whether the sample is normal or defective.
3. Classifies the defect type as `color`, `combined`, `hole`, `liquid`, or `scratch`.
4. Generates an anomaly heatmap and a predicted defect region.
5. Compares the predicted mask with ground truth when the uploaded image belongs to the dataset.
6. Shows an agent plan, review status, and retraining recommendation.
7. Lets the user submit annotation feedback.
8. Retrains the classifier from collected feedback when triggered from the UI.

## Tech Stack

- Python
- PyTorch
- FastAPI
- OpenCV
- React
- Vite

## Dataset

This project uses the **MVTec AD wood dataset**.

Expected dataset structure:

```text
data/
  wood/
    train/
      good/
        000.png
        ...
    test/
      color/
      combined/
      hole/
      liquid/
      scratch/
      good/
    ground_truth/
      color/
      combined/
      hole/
      liquid/
      scratch/
```

The project also stores user feedback here:

```text
data/
  feedback/
    color/
    combined/
    hole/
    liquid/
    scratch/
```

## Project Structure

```text
backend/        FastAPI routes, inference pipeline, agent workflow, retraining control
frontend/       React + Vite dashboard
training/       Model training scripts
models/         Trained model files
data/           Dataset and collected feedback
logs/           Prediction, feedback, retraining, and agent workflow logs
```

## Required Model Files

For inference, these files must exist in `models/`:

```text
models/classifier.pth
models/segmenter.pth
models/padim.pkl
```

If they are not available on a new machine, you can regenerate them by training from the scripts in `training/`.

## Run On A New Device

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd wood-defect-agentic-ai
```

### 2. Create and activate a Python environment

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Add the dataset

Place the MVTec wood dataset into the `data/wood/` structure shown above.

### 6. Train the required models if model files are missing

From the project root, run:

```bash
python3 training/train_padim.py
python3 training/train_segmenter.py
python3 training/train_classifier.py
```

This will create:

```text
models/padim.pkl
models/segmenter.pth
models/classifier.pth
```

### 7. Start the backend

```bash
uvicorn backend.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

### 8. Start the frontend

In another terminal:

```bash
cd frontend
npm run dev
```

Frontend usually runs at:

```text
http://127.0.0.1:5173
```

### 9. Use the app

1. Open the frontend in a browser.
2. Upload a wood image.
3. Click `Analyze Image`.
4. Review prediction, mask comparison, agent plan, and review loop.
5. If needed, submit annotation feedback.
6. Use the retraining button when the review loop recommends retraining.

## Model Training Details

### 1. Train PaDiM

Command:

```bash
python3 training/train_padim.py
```

Uses:
- `data/wood/train/good`

Output:
- `models/padim.pkl`

Purpose:
- builds the anomaly detection statistics used during inference

### 2. Train Segmenter

Command:

```bash
python3 training/train_segmenter.py
```

Uses:
- `data/wood/test/<defect_class>`
- `data/wood/ground_truth/<defect_class>`

Output:
- `models/segmenter.pth`

Purpose:
- trains the custom hybrid ResNet50-ViT model used to refine defect localization masks

### 3. Train Classifier

Command:

```bash
python3 training/train_classifier.py
```

Uses:
- `data/wood/test/<defect_class>`
- `data/feedback/<defect_class>`

Output:
- `models/classifier.pth`

Purpose:
- trains the classifier for known defect classes
- uses collected feedback samples in retraining

## Complete Development Workflow

### Train models from scratch

```bash
python3 training/train_padim.py
python3 training/train_segmenter.py
python3 training/train_classifier.py
```

### Run backend

```bash
uvicorn backend.main:app --reload
```

### Run frontend

```bash
cd frontend
npm run dev
```

## Retraining Workflow

1. Upload and analyze images in the dashboard.
2. Submit annotation feedback for incorrect or weak predictions.
3. The feedback is stored under `data/feedback/`.
4. The agent review loop checks:
   - recent prediction quality
   - recent low-confidence predictions
   - weak mask cases
   - new feedback collected after the last retrain
5. When enough evidence exists, the UI shows a retraining recommendation.
6. Start retraining from the dashboard.
7. The backend launches classifier retraining and reloads the updated model.

## Important Notes

- The backend depends on trained model files being present in `models/`.
- Ground-truth comparison works best for images that come from the dataset.
- Retraining currently updates the classifier only.
- The hybrid segmenter and PaDiM are trained separately from their own scripts.
- If you change backend code, restart the backend server.
- If you change frontend code, Vite usually hot-reloads automatically.

## Quick Verification

Check backend import:

```bash
python3 -c "import backend.main"
```

Check frontend production build:

```bash
cd frontend
npm run build
```

## API Endpoints

- `POST /predict`
  Runs the full inference pipeline on an uploaded image.

- `POST /feedback`
  Stores user-provided label and defect region feedback.

- `GET /agent/review`
  Returns the current workflow review summary and retraining recommendation.

- `GET /retrain/status`
  Returns current retraining status and progress.

## Current Agentic AI Design

This project now uses a **local workflow-based agentic layer**, not an external API-based LLM.

The agentic part is responsible for:
- deciding next actions from prediction quality
- assigning workflow states and priorities
- tracking samples in review queues
- monitoring post-retraining behavior
- recommending retraining from accumulated evidence

## License And Dataset Notes

- Check `data/wood/license.txt` and `data/wood/readme.txt` for dataset-related notes.
- If you publish the repo, make sure the dataset license allows redistribution, or provide download/setup instructions instead of uploading the raw dataset.
