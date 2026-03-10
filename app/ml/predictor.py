from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = Path(__file__).parent / "model" / "final_sinhala_mood_model"

# device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# lazy-load globals
tokenizer = None
model = None
id2label = None


def _model_files_present() -> bool:
    candidates = [
        "pytorch_model.bin",
        "model.safetensors",
        "tf_model.h5",
        "model.ckpt.index",
        "flax_model.msgpack"
    ]
    return any((MODEL_DIR / name).exists() for name in candidates)


def _load_model() -> None:
    global tokenizer, model, id2label
    if tokenizer is not None and model is not None and id2label is not None:
        return
    if not _model_files_present():
        raise RuntimeError(
            f"Model files not found in {MODEL_DIR}. "
            "Place the trained model files there before calling prediction."
        )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model = model.to(device)
    model.eval()

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
