import cv2
from PyQt6.QtGui import QImage, QPixmap
import config
 
 
def draw_boxes(image, results):
    """
    Draw bounding boxes for every 'person' detection.
 
    Parameters
    ----------
    image   : numpy array (BGR) from cv2.imread
    results : ultralytics Results object from detector.detect()
 
    Returns
    -------
    image : numpy array with boxes drawn on it
    """
    for result in results:
        for box in result.boxes:
            label = result.names[int(box.cls)]
            if label != config.TARGET_CLASS:
                continue
 
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
 
            # Draw rectangle
            cv2.rectangle(
                image,
                (x1, y1), (x2, y2),
                config.BOX_COLOR,
                config.BOX_THICKNESS
            )
 
            # Draw label background + text
            text = f"Person  {conf:.0%}"
            (tw, th), _ = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX,
                config.FONT_SCALE, 1
            )
            cv2.rectangle(image, (x1, y1 - th - 8), (x1 + tw + 6, y1), config.BOX_COLOR, -1)
            cv2.putText(
                image, text,
                (x1 + 3, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                config.FONT_SCALE,
                (0, 0, 0),   # black text on coloured background
                1,
                cv2.LINE_AA
            )
 
    return image
 
 
def cv2_to_pixmap(image) -> QPixmap:
    """
    Convert a BGR numpy array to a QPixmap for display in QLabel.
    """
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)
 