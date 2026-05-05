from pathlib import Path
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.services.s3_model_loader import download_s3_folder

DEFAULT_LOCAL_MODEL_DIR = Path(__file__).parent / "model" / "final_sinhala_mood_model"

# device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# lazy-load globals
tokenizer = None
model = None
id2label = None
MODEL_DIR = None


def _resolve_model_dir() -> Path:
    is_production = os.getenv("PRODUCTION", "false").strip().lower() == "true"
    if is_production:
        bucket = os.getenv("S3_MODEL_BUCKET", "research-models-prod").strip()
        prefix = os.getenv("S3_SINHALA_MODEL_PREFIX", "mood_prediction_model/final_sinhala_mood_model/").strip()
        local_dir = os.getenv("LOCAL_SINHALA_MODEL_DIR", "/app/downloaded_models/final_sinhala_mood_model").strip()
        print(f"[Sinhala Mood Predictor] PRODUCTION=true, downloading model from S3: s3://{bucket}/{prefix}")
        downloaded_dir = download_s3_folder(bucket=bucket, prefix=prefix, local_dir=local_dir)
        print(f"[Sinhala Mood Predictor] Using local downloaded model directory: {downloaded_dir}")
        return Path(downloaded_dir)

    local_env_dir = os.getenv("LOCAL_MODEL_PATH", "").strip()
    if local_env_dir:
        print(f"[Sinhala Mood Predictor] PRODUCTION=false, using LOCAL_MODEL_PATH: {local_env_dir}")
        return Path(local_env_dir)
    print(f"[Sinhala Mood Predictor] PRODUCTION=false, using default local model path: {DEFAULT_LOCAL_MODEL_DIR}")
    return DEFAULT_LOCAL_MODEL_DIR


def _model_files_present(model_dir: Path) -> bool:
    candidates = [
        "pytorch_model.bin",
        "model.safetensors",
        "tf_model.h5",
        "model.ckpt.index",
        "flax_model.msgpack"
    ]
    return any((model_dir / name).exists() for name in candidates)


def _load_model() -> None:
    global tokenizer, model, id2label, MODEL_DIR
    if tokenizer is not None and model is not None and id2label is not None:
        return
    MODEL_DIR = _resolve_model_dir()

    if not _model_files_present(MODEL_DIR):
        raise RuntimeError(
            f"Model files not found in {MODEL_DIR}. "
            "Place the trained model files there before calling prediction."
        )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, local_files_only=True)
    model = model.to(device)
    model.eval()
    print(f"[Sinhala Mood Predictor] Model loaded successfully from: {MODEL_DIR}")

    raw_id2label = model.config.id2label
    id2label = {int(k): v for k, v in raw_id2label.items()} if isinstance(list(raw_id2label.keys())[0], str) else raw_id2label

    fallback = {0: "Bad", 1: "Normal", 2: "Happy"}
    if any(str(v).startswith("LABEL_") for v in id2label.values()):
        id2label = fallback


def predict_with_probs(text: str):
    _load_model()
    text = text.strip()
    if not text:
        return {
            "mood": "Unknown",
            "confidence": 0.0,
            "probs": {}
        }

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1).squeeze(0)

    pred_id = int(torch.argmax(probs).item())
    confidence = float(probs[pred_id].item())
    probs_dict = {id2label[i]: float(probs[i].item()) for i in range(probs.shape[0])}

    return {
        "mood": id2label.get(pred_id, str(pred_id)),
        "confidence": confidence,
        "probs": probs_dict
    }
