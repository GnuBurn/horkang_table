import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QGridLayout, QVBoxLayout, QHBoxLayout,
                             QFrame, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal


class CameraWidget(QFrame):
    delete_requested = pyqtSignal(object)

    def __init__(self, cam_id):
        super().__init__()
        self.cam_id = cam_id
        self.table_count = 0
        self.setStyleSheet(
            "background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px;")

        self.main_layout = QVBoxLayout(self)

        self.top_bar = QHBoxLayout()
        self.id_label = QLabel(f"CH {self.cam_id:02d}")
        self.id_label.setStyleSheet(
            "color: #00ffcc; font-weight: bold; border: none;")

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet(
            "background: #444; color: white; border-radius: 10px; border: none;")
        self.close_btn.clicked.connect(
            lambda: self.delete_requested.emit(self))

        self.top_bar.addWidget(self.id_label)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.close_btn)
        self.main_layout.addLayout(self.top_bar)

        self.content_layout = QHBoxLayout()

        self.video_area = QLabel("NO SIGNAL")
        self.video_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_area.setStyleSheet(
            "background: #000; color: #444; border-radius: 4px;")

        self.info_panel = QVBoxLayout()
        self.info_panel.setSpacing(2)

        self.lbl_title = QLabel("TABLES")
        self.lbl_title.setStyleSheet(
            "font-size: 10px; color: #888; border: none;")

        self.count_label = QLabel(f"{self.table_count}")
        self.count_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: white; border: none;")

        self.info_panel.addWidget(self.lbl_title)
        self.info_panel.addWidget(self.count_label)
        self.info_panel.addStretch()

        self.content_layout.addWidget(self.video_area, stretch=7)
        self.content_layout.addLayout(self.info_panel, stretch=3)

        self.main_layout.addLayout(self.content_layout)


class CCTVManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart HorKang Monitor v1.0")
        self.resize(1200, 750)
        self.setStyleSheet("background-color: #121212; color: #e0e0e0;")

        self.all_cameras = []
        self.current_page = 0
        self.max_per_page = 6

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout, stretch=5)

        self.setup_sidebar()

    def setup_sidebar(self):
        self.sidebar = QVBoxLayout()
        self.sidebar.setContentsMargins(10, 20, 10, 20)

        self.add_btn = QPushButton("+ ADD CAMERA")
        self.add_btn.setFixedHeight(50)
        self.add_btn.setStyleSheet(
            "background: #0078d7; font-weight: bold; border-radius: 5px;")
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

        self.sidebar.addWidget(self.add_btn)
        self.sidebar.addSpacing(30)
        self.sidebar.addWidget(QLabel("NAVIGATION"))
        self.sidebar.addWidget(self.page_info)
        self.sidebar.addLayout(self.nav_layout)
        self.sidebar.addStretch()

        self.main_layout.addLayout(self.sidebar, stretch=1)

    def add_camera(self):
        new_cam = CameraWidget(len(self.all_cameras) + 1)
        new_cam.delete_requested.connect(self.remove_camera)
        self.all_cameras.append(new_cam)
        self.update_view()

    def remove_camera(self, cam_widget):
        self.all_cameras.remove(cam_widget)
        cam_widget.deleteLater()
        if self.current_page > 0 and len(self.all_cameras) <= self.current_page * self.max_per_page:
            self.current_page -= 1
        self.update_view()

    def update_view(self):
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        start = self.current_page * self.max_per_page
        end = start + self.max_per_page
        page_items = self.all_cameras[start:end]

        for i, cam in enumerate(page_items):
            self.grid_layout.addWidget(cam, i // 3, i % 3)

        total_pages = max(1, (len(self.all_cameras) + 5) // 6)
        self.page_info.setText(f"PAGE {self.current_page + 1} / {total_pages}")

        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(end < len(self.all_cameras))

    def next_page(self):
        self.current_page += 1
        self.update_view()

    def prev_page(self):
        self.current_page -= 1
        self.update_view()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CCTVManager()
    window.show()
    sys.exit(app.exec())
