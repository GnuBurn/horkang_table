from ultralytics import YOLO
import config

class AnomalyDetector:
    def __init__(self):
        self.model = YOLO(config.ANOMALY_MODEL_NAME)

    def detect(self, frame):
        results = self.model(
            frame, 
            conf=config.ANOMALY_THRESHOLD, 
            verbose=False
        )
        positions = []
        for r in results:
            for box in r.boxes:
                positions.append(box.xyxy[0].tolist())
        return results, positions, len(positions)