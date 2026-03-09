import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
from PIL import Image

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

CLASS_NAMES = ["Happy", "Sad", "Angry", "Fear"]
IMG_SIZE = 320

PREPROCESS = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

class EfficientNetClassifier(nn.Module):
    def __init__(self, num_classes=4, dropout=0.35):
        super().__init__()
        backbone = models.efficientnet_b2(weights=None)
        in_features = backbone.classifier[1].in_features
        backbone.classifier = nn.Identity()

        self.backbone = backbone
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(in_features, num_classes)

    def forward(self, x):
        features = self.backbone(x)
        features = self.dropout(features)
        return self.head(features)

def load_emotion_model(weights_path: str):
    model = EfficientNetClassifier(num_classes=4, dropout=0.35)
    state_dict = torch.load(weights_path, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model

@torch.no_grad()
def predict_emotion(model, pil_img: Image.Image):
    img_tensor = PREPROCESS(pil_img.convert("RGB")).unsqueeze(0).to(DEVICE)
    logits = model(img_tensor)
    probs = torch.softmax(logits, dim=1)[0]
    pred_idx = torch.argmax(probs).item()

    return {
        "label": CLASS_NAMES[pred_idx],
        "confidence": float(probs[pred_idx]),
        "probabilities": {
            CLASS_NAMES[i]: float(probs[i]) for i in range(len(CLASS_NAMES))
        }
    }