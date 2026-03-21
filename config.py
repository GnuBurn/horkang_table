HUMAN_MODEL_NAME = "runs\detect\human_detector_v2\weights\\best.pt"
ANOMALY_MODEL_NAME = "object_model\\anomaly_model_v1.pt"
 
# Only detect this class from COCO labels
TARGET_CLASS = "person"
 
# Minimum confidence to count as a detection
CONFIDENCE_THRESHOLD = 0.5
 
# Sample images folder
INPUT_DIR = 'sample_images'
 
# Saved output images folder
OUTPUT_DIR = "output"
 
# Bounding box colour
BOX_COLOR = (0, 255, 204)
TEXT_COLOR = (0, 255, 204)
BOX_THICKNESS = 2
FONT_SCALE = 0.55