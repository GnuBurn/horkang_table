import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPixmap

def draw_detections(image, h_results, a_results):
    """
    Draws boxes for humans (Green) and anomalies (Orange).
    NO LABELS are added here.
    """
    for r in h_results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
    for r in a_results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 165, 255), 2)

def draw_table_zones(image, tables, table_statuses):
    """
    Draws polygons for tables and adds the Table ID and Status label.
    """
    for table in tables:
        t_id = table['table_id']
        status = table_statuses.get(t_id, "free")
        
        if status == "occupied":
            color = (0, 0, 255) # Red
        elif status == "reserved":
            color = (0, 165, 255) # Orange
        elif status == "exceeded":
            color = (128, 0, 128) # Purple
        else:
            color = (0, 255, 0) # Green (free)
            
        pts = np.array(table['points'], np.int32)
        
        cv2.polylines(image, [pts], isClosed=True, color=color, thickness=3)
        
        label_pos = (table['points'][0][0], table['points'][0][1] - 10)
        text = f"{t_id}: {status}"
        cv2.putText(image, text, label_pos, 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    

def cv2_to_pixmap(cv_img):
    height, width, _ = cv_img.shape
    bytes_per_line = 3 * width
    q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
    return QPixmap.fromImage(q_img)