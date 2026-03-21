import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel,
                              QGridLayout, QVBoxLayout, QHBoxLayout,
                              QPushButton)
from PyQt6.QtCore import Qt

from camera_widget import CameraWidget
import config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def _get_sample_images() -> list[str]:
    """Return sorted list of image paths inside config.INPUT_DIR."""
    if not os.path.isdir(config.INPUT_DIR):
        return []
    files = sorted(os.listdir(config.INPUT_DIR))
    return [
        os.path.join(config.INPUT_DIR, f)
        for f in files
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    ]


class CCTVManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Restaurant Monitor v1.0")
        self.resize(1200, 750)
        self.setStyleSheet("background-color: #121212; color: #e0e0e0;")

        self.all_cameras: list[CameraWidget] = []
        self.current_page = 0
        self.max_per_page = 6

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout, stretch=5)

        self._setup_sidebar()

    def _setup_sidebar(self):
        self.sidebar = QVBoxLayout()
        self.sidebar.setContentsMargins(10, 20, 10, 20)

        self.add_btn = QPushButton("+ ADD CAMERA")
        self.add_btn.setFixedHeight(50)
        self.add_btn.setStyleSheet(
            "background: #0078d7; font-weight: bold; border-radius: 5px;"
        )
        self.add_btn.clicked.connect(self.add_camera)

        self.page_info = QLabel("PAGE 1 / 1")
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        for btn in [self.prev_btn, self.next_btn]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("background: #333; border-radius: 20px;")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.nav_layout.addWidget(self.prev_btn)
        self.nav_layout.addWidget(self.next_btn)

        self.img_status = QLabel()
        self.img_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_status.setStyleSheet("font-size: 10px; color: #888;")
        self._refresh_img_status()

        self.total_label_title = QLabel("TOTAL PERSONS")
        self.total_label_title.setStyleSheet("font-size: 10px; color: #888;")
        self.total_label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.total_count = QLabel("0")
        self.total_count.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #00ffcc;"
        )
        self.total_count.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.sidebar.addWidget(self.add_btn)
        self.sidebar.addSpacing(8)
        self.sidebar.addWidget(self.img_status)
        self.sidebar.addSpacing(20)
        self.sidebar.addWidget(QLabel("NAVIGATION"))
        self.sidebar.addWidget(self.page_info)
        self.sidebar.addLayout(self.nav_layout)
        self.sidebar.addStretch()
        self.sidebar.addWidget(self.total_label_title)
        self.sidebar.addWidget(self.total_count)
        self.sidebar.addSpacing(20)

        self.main_layout.addLayout(self.sidebar, stretch=1)

    def add_camera(self):
        """
        Pick the next image from data/samples/ (cycles if more cameras than images),
        create a tile and run detection immediately — no file dialog.
        """
        images = _get_sample_images()

        new_cam = CameraWidget(len(self.all_cameras) + 1)
        new_cam.delete_requested.connect(self.remove_camera)
        self.all_cameras.append(new_cam)
        self.update_view()

        if images:
            path = images[(len(self.all_cameras) - 1) % len(images)]
            new_cam.load_image(path)
        else:
            new_cam.show_no_signal("No images found\nin data/samples/")

        self._refresh_total()
        self._refresh_img_status()

    def remove_camera(self, cam_widget: CameraWidget):
        self.all_cameras.remove(cam_widget)
        cam_widget.deleteLater()
        if (self.current_page > 0 and
                len(self.all_cameras) <= self.current_page * self.max_per_page):
            self.current_page -= 1
        self.update_view()
        self._refresh_total()
        self._refresh_img_status()

    def update_view(self):
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        start = self.current_page * self.max_per_page
        end = start + self.max_per_page
        for i, cam in enumerate(self.all_cameras[start:end]):
            self.grid_layout.addWidget(cam, i // 3, i % 3)

        total_pages = max(1, (len(self.all_cameras) + self.max_per_page - 1) // self.max_per_page)
        self.page_info.setText(f"PAGE {self.current_page + 1} / {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(end < len(self.all_cameras))

    def next_page(self):
        self.current_page += 1
        self.update_view()

    def prev_page(self):
        self.current_page -= 1
        self.update_view()

    def _refresh_total(self):
        total = sum(cam.person_count for cam in self.all_cameras)
        self.total_count.setText(str(total))

    def _refresh_img_status(self):
        images = _get_sample_images()
        n = len(images)
        used = len(self.all_cameras)
        self.img_status.setText(f"{min(used, n)} / {n} images loaded")
        no_images = n == 0
        self.add_btn.setEnabled(not no_images)
        self.add_btn.setStyleSheet(
            "background: #444; font-weight: bold; border-radius: 5px; color: #888;"
            if no_images else
            "background: #0078d7; font-weight: bold; border-radius: 5px;"
        )