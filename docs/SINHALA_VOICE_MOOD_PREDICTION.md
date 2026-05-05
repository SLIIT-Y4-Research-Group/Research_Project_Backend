# Sinhala Voice Mood Prediction Documentation

## Overview

This module predicts student mood from Sinhala voice-to-text content using a fine-tuned Transformer classification model.

Configured local model path:

`D:\Research\Research Project Backend\backend\app\ml\model\final_sinhala_mood_model`

In code (default path):

`app/ml/model/final_sinhala_mood_model`

The predictor is implemented in:

- `app/ml/predictor.py`

---

## Mood Classes

The model returns one of these mood labels:

- `Bad`
- `Normal`
- `Happy`

If model label mapping is generic (like `LABEL_0`), the fallback mapping used is:

- `0 -> Bad`
- `1 -> Normal`
- `2 -> Happy`

---

## Requirements

## 1. Python Packages

Required runtime packages:

- `torch`
- `transformers`

Optional for production S3 model download flow:

- `boto3`

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Model Files

The local folder `app/ml/model/final_sinhala_mood_model` must include Hugging Face model artifacts, typically:

- `config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `special_tokens_map.json`
- `model.safetensors` or `pytorch_model.bin`

---

## Environment Configuration

For local development:

```env
PRODUCTION=false
LOCAL_MODEL_PATH=app/ml/model/final_sinhala_mood_model
```

For production with S3 download:

```env
PRODUCTION=true
AWS_REGION=ap-south-1
S3_MODEL_BUCKET=research-models-prod
S3_SINHALA_MODEL_PREFIX=models/sinhala-mood/
LOCAL_SINHALA_MODEL_DIR=/app/downloaded_models/sinhala-mood
```

---

## Prediction Flow

1. Sinhala voice is converted to text by the client or upstream service.
2. Text is sent to backend mood prediction endpoint/service.
3. `app/ml/predictor.py` lazy-loads tokenizer and model on first use.
4. Text is tokenized with truncation (`max_length=128`).
5. Model produces logits and softmax probabilities.
6. Response includes:
   - predicted `mood`
   - `confidence`
   - per-class `probs`

---

## Response Shape

Prediction output format:

```json
{
  "mood": "Happy",
  "confidence": 0.91,
  "probs": {
    "Bad": 0.03,
    "Normal": 0.06,
    "Happy": 0.91
  }
}
```

If input text is empty:

```json
{
  "mood": "Unknown",
  "confidence": 0.0,
  "probs": {}
}
```

---

## Operational Notes

- Model is loaded once and cached in memory.
- Device is auto-selected:
  - `cuda` if available
  - otherwise `cpu`
- First prediction is slower due to lazy loading.

---

## Troubleshooting

1. `Model files not found`:
- Check `LOCAL_MODEL_PATH` and ensure model files exist.

2. Wrong mood labels like `LABEL_0`:
- Fallback mapping to `Bad/Normal/Happy` is applied automatically.

3. Slow first request:
- Expected behavior due to model initialization.

4. Production S3 download errors:
- Verify IAM role, bucket name, and prefix.

