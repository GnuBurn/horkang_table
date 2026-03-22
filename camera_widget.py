import cv2
import json
import numpy as np
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from human_detector import HumanDetector
from anomaly_detector import AnomalyDetector
from visualizer import draw_detections, draw_table_zones, cv2_to_pixmap

class CameraWidget(QFrame):
    delete_requested = pyqtSignal(object)
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
    
    def set_full_screen(self, is_full):
        """Toggle full screen mode for this camera widget."""
        if is_full:
            self.close_btn.hide()
            self.setFixedSize(1200, 700)
        else:
            self.close_btn.show()
            self.setFixedSize(500, 350)

    def load_image(self, image_path, channel_key=None):
        print(f"Loading image: {image_path} for channel: {channel_key}")
        image = cv2.imread(image_path)
        if image is None: return
    
        h, w = image.shape[:2]
        h_det, a_det, templates = self.get_resources()
        print(templates)
        key = channel_key.lower().replace(" ", "_") if channel_key else None
        print(f"Using template key: {key}")
        
        h_results, h_positions, h_count = h_det.detect(image_path)
        a_results, a_positions, a_count = a_det.detect(image_path)

        occupied_ids = []
        tables = templates.get(key, {}).get('tables', [])
        annotated = image.copy()

        draw_detections(annotated, h_results, a_results)
        draw_table_zones(annotated, tables, occupied_ids)

        self.person_count = h_count
        self.video_area.setPixmap(cv2_to_pixmap(annotated))
        self.count_label.setText(str(h_count))