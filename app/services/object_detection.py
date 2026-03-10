from typing import Dict, Any, List
from PIL import Image
from ultralytics import YOLO

_model = None

def load_detector(weights_path: str):
    global _model
    _model = YOLO(weights_path)
    return _model

def detect_objects(detector, pil_img: Image.Image, score_thresh: float = 0.25) -> Dict[str, Any]:
    w, h = pil_img.size

    results = detector.predict(
        source=pil_img,
        conf=score_thresh,
        iou=0.45,
        verbose=False
    )
    r = results[0]

    detections: List[Dict[str, Any]] = []

    if r.boxes is not None and len(r.boxes) > 0:
        xyxy = r.boxes.xyxy.cpu().numpy()
        conf = r.boxes.conf.cpu().numpy()
        cls = r.boxes.cls.cpu().numpy().astype(int)
        names = r.names

        for (x1, y1, x2, y2), c, k in zip(xyxy, conf, cls):
            detections.append({
                "class_id": int(k),
                "label": str(names[int(k)]),
                "score": float(c),
                "box": {
                    "x1": float(x1),
                    "y1": float(y1),
                    "x2": float(x2),
                    "y2": float(y2)
                },
                "box_norm": {
                    "x1": float(x1) / w,
                    "y1": float(y1) / h,
                    "x2": float(x2) / w,
                    "y2": float(y2) / h
                }
            })

    return {
        "count": len(detections),
        "detections": detections
    }