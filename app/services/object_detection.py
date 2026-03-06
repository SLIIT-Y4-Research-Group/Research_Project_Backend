from typing import Dict, Any, List
import torch
from PIL import Image
from torchvision import transforms
import torchvision

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TF = transforms.Compose([transforms.ToTensor()])

COCO_NAMES = [
    "__background__",
    "person","bicycle","car","motorcycle","airplane","bus","train","truck","boat",
    "traffic light","fire hydrant","stop sign","parking meter","bench",
    "bird","cat","dog","horse","sheep","cow","elephant","bear","zebra","giraffe",
    "backpack","umbrella","handbag","tie","suitcase",
    "frisbee","skis","snowboard","sports ball","kite","baseball bat","baseball glove",
    "skateboard","surfboard","tennis racket",
    "bottle","wine glass","cup","fork","knife","spoon","bowl",
    "banana","apple","sandwich","orange","broccoli","carrot","hot dog","pizza","donut","cake",
    "chair","couch","potted plant","bed","dining table","toilet","tv","laptop","mouse","remote","keyboard",
    "cell phone","microwave","oven","toaster","sink","refrigerator",
    "book","clock","vase","scissors","teddy bear","hair drier","toothbrush"
]

def load_detector():
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights="DEFAULT")
    model.to(DEVICE)
    model.eval()
    return model

@torch.no_grad()
def detect_objects(detector, pil_img: Image.Image, score_thresh: float = 0.60) -> Dict[str, Any]:
    x = TF(pil_img.convert("RGB")).to(DEVICE)
    out = detector([x])[0]

    boxes = out["boxes"].detach().cpu().numpy()
    labels = out["labels"].detach().cpu().numpy()
    scores = out["scores"].detach().cpu().numpy()

    detections: List[Dict[str, Any]] = []
    for box, lab, sc in zip(boxes, labels, scores):
        sc = float(sc)
        if sc < score_thresh:
            continue

        lab = int(lab)
        name = COCO_NAMES[lab] if 0 <= lab < len(COCO_NAMES) else f"coco_{lab}"
        x1, y1, x2, y2 = [float(v) for v in box.tolist()]

        detections.append({
            "class_id": lab,
            "label": name,
            "score": sc,
            "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        })

    return {"count": len(detections), "detections": detections}