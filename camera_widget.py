# ─────────────────────────────────────────
#  camera_widget.py  –  Single camera tile
# ─────────────────────────────────────────

import cv2
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout,
                              QHBoxLayout, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from human_detector import HumanDetector
from visualizer import draw_boxes, cv2_to_pixmap


class CameraWidget(QFrame):
    delete_requested = pyqtSignal(object)

    # One shared model instance across all tiles (loads only once)
    _detector: HumanDetector | None = None

    @classmethod
    def get_detector(cls) -> HumanDetector:
        if cls._detector is None:
            cls._detector = HumanDetector()
        return cls._detector

    # ── Construction ───────────────────────────────────────────────
    def __init__(self, cam_id: int):
        super().__init__()
        self.cam_id = cam_id
        self.person_count = 0

        self.setStyleSheet(
            "background-color: #1a1a1a;"
            "border: 1px solid #333;"
            "border-radius: 8px;"
        )

        self.main_layout = QVBoxLayout(self)

        # 1. Top bar
        top_bar = QHBoxLayout()
        self.id_label = QLabel(f"CH {self.cam_id:02d}")
        self.id_label.setStyleSheet(
            "color: #00ffcc; font-weight: bold; border: none;"
        )
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet(
            "background: #444; color: white; border-radius: 10px; border: none;"
        )
        self.close_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        top_bar.addWidget(self.id_label)
        top_bar.addStretch()
        top_bar.addWidget(self.close_btn)
        self.main_layout.addLayout(top_bar)

        # 2. Content: video | info
        content = QHBoxLayout()

        self.video_area = QLabel("NO SIGNAL")
        self.video_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_area.setStyleSheet(
            "background: #000; color: #444; border-radius: 4px;"
        )
        self.video_area.setScaledContents(True)

        info = QVBoxLayout()
        info.setSpacing(2)

        self.lbl_title = QLabel("PERSONS")
        self.lbl_title.setStyleSheet("font-size: 10px; color: #888; border: none;")

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: white; border: none;"
        )

        # Image filename label (small, below count)
        self.filename_label = QLabel("")
        self.filename_label.setStyleSheet(
            "font-size: 9px; color: #555; border: none;"
        )
        self.filename_label.setWordWrap(True)

        info.addWidget(self.lbl_title)
        info.addWidget(self.count_label)
        info.addSpacing(8)
        info.addWidget(self.filename_label)
        info.addStretch()

        content.addWidget(self.video_area, stretch=7)
        content.addLayout(info, stretch=3)
        self.main_layout.addLayout(content)

    # ── Public API ─────────────────────────────────────────────────
    def load_image(self, image_path: str):
        """
        Read image from disk, run YOLOv8 detection,
        draw bounding boxes, and update the tile — all automatically.
        """
        image = cv2.imread(image_path)
        if image is None:
            self.show_no_signal("File not found")
            return

        detector = CameraWidget.get_detector()
        results, count = detector.detect(image_path)

        annotated = draw_boxes(image, results)
        pixmap = cv2_to_pixmap(annotated)

        self._update_display(pixmap, count, image_path)

    def show_no_signal(self, message: str = "NO SIGNAL"):
        """Show a text message in the video area (no image available)."""
        self.video_area.setPixmap(QPixmap())   # clear any previous image
        self.video_area.setText(message)
        self.count_label.setText("—")
        self.filename_label.setText("")

    # ── Private ────────────────────────────────────────────────────
    def _update_display(self, pixmap: QPixmap, person_count: int, image_path: str):
        self.person_count = person_count
        self.video_area.setText("")
        self.video_area.setPixmap(pixmap)
        self.count_label.setText(str(person_count))
        # Show just the filename, not the full path
        self.filename_label.setText(image_path.split("/")[-1])