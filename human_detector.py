from ultralytics import YOLO
import config
 
 
class HumanDetector:
    """Loads YOLOv8 once and runs inference on demand."""
 
    def __init__(self):
        self.model = YOLO(config.MODEL_NAME)   # auto-downloads on first run
        print(f"[Detector] Model loaded: {config.MODEL_NAME}")
 
    def detect(self, image_path: str):
        """
        Run detection on an image file.
 
        Returns
        -------
        results : ultralytics Results object
            Access .boxes for bounding-box data.
        person_count : int
            Number of 'person' detections above threshold.
        """
        results = self.model(
            image_path,
            conf=config.CONFIDENCE_THRESHOLD,
            verbose=False
        )
 
        person_count = 0
        for result in results:
            for box in result.boxes:
                label = result.names[int(box.cls)]
                if label == config.TARGET_CLASS:
                    person_count += 1
 
        return results, person_count