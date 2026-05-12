from ultralytics import YOLO
import config

class HumanDetector:
    def __init__(self):
        self.model = YOLO(config.HUMAN_MODEL_NAME)

    def detect(self, frame):
        results = self.model(
            frame, 
            conf=config.CONFIDENCE_THRESHOLD, 
            verbose=False
        )
        positions = []
        for r in results:
            for box in r.boxes:
                positions.append(box.xyxy[0].tolist())
        return results, positions, len(positions)