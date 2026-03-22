from ultralytics import YOLO
import config

class AnomalyDetector:
    def __init__(self):
        self.model = YOLO(config.ANOMALY_MODEL_NAME)

    def detect(self, image_path):
        results = self.model(
            image_path, 
            conf=config.ANOMALY_THRESHOLD, 
            verbose=False
        )
        print(f"Anomaly Detection: {len(results[0].boxes)} anomalies detected.")
        positions = []
        for r in results:
            for box in r.boxes:
                positions.append(box.xyxy[0].tolist())
        return results, positions, len(positions)