import cv2
import json
import numpy as np
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap
from shapely.geometry import Polygon, box
from human_detector import HumanDetector
from anomaly_detector import AnomalyDetector
from visualizer import draw_detections, draw_table_zones, cv2_to_pixmap

class CameraWidget(QFrame):
    delete_requested = pyqtSignal(object)
    status_updated = pyqtSignal(dict)
    _h_detector = None
    _a_detector = None
    _templates = {}

    @classmethod
    def get_resources(cls):
        if cls._h_detector is None: cls._h_detector = HumanDetector()
        if cls._a_detector is None: cls._a_detector = AnomalyDetector()
        if not cls._templates:
            try:
                with open('channel_templates.json', 'r') as f:
                    cls._templates = json.load(f)['channels']
                    print("Loaded channel templates successfully.")
            except: print("Failed to load channel templates. Make sure 'channel_template.json' exists and is properly formatted.")
        return cls._h_detector, cls._a_detector, cls._templates

    def __init__(self, cam_id):
        super().__init__()
        self.cam_id = cam_id
        self.person_count = 0

        self.setFixedSize(500, 350)
        self.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px;")
        
        self.main_layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        self.id_label = QLabel(f"CH {self.cam_id:02d}")
        self.id_label.setStyleSheet("color: #00ffcc; font-weight: bold; border: none;")
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("background: #444; color: white; border-radius: 10px; border: none;")
        self.close_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        top_bar.addWidget(self.id_label)
        top_bar.addStretch()
        top_bar.addWidget(self.close_btn)
        self.main_layout.addLayout(top_bar)

        content = QHBoxLayout()
        self.video_area = QLabel("NO SIGNAL")
        self.video_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_area.setStyleSheet("background: #000; color: #444; border-radius: 4px;")
        self.video_area.setScaledContents(True)

        info = QVBoxLayout()
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; border: none;")
        info.addWidget(QLabel("PERSONS", styleSheet="font-size: 10px; color: #888; border: none;"))
        info.addWidget(self.count_label)
        info.addStretch()
        
        content.addWidget(self.video_area, stretch=7)
        content.addLayout(info, stretch=3)
        self.main_layout.addLayout(content)
        
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        self.channel_key = None
        self.table_states = {}
        self.last_time = 0
    
    def set_full_screen(self, is_full):
        """Toggle full screen mode for this camera widget."""
        if is_full:
            self.close_btn.hide()
            self.setMinimumSize(800, 600)
            self.setMaximumSize(16777215, 16777215)
        else:
            self.close_btn.show()
            self.setFixedSize(500, 350)

    def cleanup(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()

    def deleteLater(self):
        self.cleanup()
        super().deleteLater()

    def load_video(self, video_path, channel_key=None):
        print(f"Loading video: {video_path} for channel: {channel_key}")
        self.cap = cv2.VideoCapture(video_path)
        self.channel_key = channel_key.lower().replace(" ", "_") if channel_key else None
        
        h_det, a_det, templates = self.get_resources()
        tables = templates.get(self.channel_key, {}).get('tables', [])
        
        for table in tables:
            t_id = table['table_id']
            self.table_states[t_id] = {
                "status": "free",
                "human_timer": 0,
                "object_timer": 0,
                "none_timer": 0,
                "reserved_start_time": 0
            }
            
        self.last_time = 0
        self.timer.start(1) # ~30fps

    def process_frame(self):
        if not self.cap or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.last_time = 0
            return
            
        current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        dt = current_time - self.last_time
        if dt < 0: dt = 0
        self.last_time = current_time
        
        h_det, a_det, templates = self.get_resources()
        h_results, h_positions, h_count = h_det.detect(frame)
        a_results, a_positions, a_count = a_det.detect(frame)
        
        self.person_count = h_count
        self.count_label.setText(str(h_count))
        
        tables = templates.get(self.channel_key, {}).get('tables', [])
        table_statuses = {}
        
        for table in tables:
            t_id = table['table_id']
            pts = np.array(table['points'], np.int32)
            
            # Use shapely for area intersection
            try:
                table_poly = Polygon(table['points'])
            except Exception:
                table_poly = None
            
            has_human = False
            for pos in h_positions:
                if table_poly and table_poly.is_valid:
                    human_box = box(pos[0], pos[1], pos[2], pos[3])
                    if table_poly.intersects(human_box):
                        intersect_area = table_poly.intersection(human_box).area
                        if intersect_area / human_box.area > 0.15:
                            has_human = True
                            break
                else:
                    # Fallback if polygon is invalid
                    cx, cy = (pos[0]+pos[2])/2, pos[3]
                    if cv2.pointPolygonTest(pts, (cx, cy), False) >= 0:
                        has_human = True
                        break
                    
            has_object = False
            if not has_human:
                for pos in a_positions:
                    cx, cy = (pos[0]+pos[2])/2, pos[3]
                    if cv2.pointPolygonTest(pts, (cx, cy), False) >= 0:
                        has_object = True
                        break
                        
            state_data = self.table_states.get(t_id)
            if not state_data: continue
            
            if has_human:
                state_data["human_timer"] += dt
                state_data["object_timer"] = 0
                state_data["none_timer"] = 0
            elif has_object:
                state_data["object_timer"] += dt
                state_data["human_timer"] = 0
                state_data["none_timer"] = 0
            else:
                state_data["none_timer"] += dt
                state_data["human_timer"] = 0
                state_data["object_timer"] = 0
                
            current_status = state_data["status"]
            
            if current_status == "free":
                if state_data["human_timer"] >= 5:
                    state_data["status"] = "occupied"
                elif state_data["object_timer"] >= 5:
                    state_data["status"] = "reserved"
                    state_data["reserved_start_time"] = current_time
            elif current_status == "occupied":
                if state_data["none_timer"] >= 5:
                    state_data["status"] = "free"
                elif state_data["object_timer"] >= 5:
                    state_data["status"] = "reserved"
                    state_data["reserved_start_time"] = current_time
            elif current_status == "reserved":
                time_in_reserved = current_time - state_data["reserved_start_time"]
                if time_in_reserved >= 15:
                    state_data["status"] = "exceeded"
                elif state_data["human_timer"] >= 5:
                    state_data["status"] = "occupied"
                elif state_data["none_timer"] >= 5:
                    state_data["status"] = "free"
            elif current_status == "exceeded":
                if state_data["none_timer"] > 0:
                    state_data["status"] = "free"
                elif state_data["human_timer"] >= 5:
                    state_data["status"] = "occupied"
                    
            table_statuses[t_id] = state_data["status"]
            
        annotated = frame.copy()
        draw_detections(annotated, h_results, a_results)
        draw_table_zones(annotated, tables, table_statuses)
        
        self.video_area.setPixmap(cv2_to_pixmap(annotated))
        self.status_updated.emit(table_statuses)