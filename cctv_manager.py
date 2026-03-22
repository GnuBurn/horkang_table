import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel, QGridLayout, 
                             QVBoxLayout, QHBoxLayout, QPushButton, 
                             QFileDialog, QInputDialog, QStackedWidget)
from PyQt6.QtCore import Qt
from camera_widget import CameraWidget

class CCTVManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Library Monitor v1.0")
        self.setFixedSize(1280, 800)
        self.setStyleSheet("background-color: #121212; color: #e0e0e0;")

        self.all_cameras = []
        self.current_page = 0
        self.max_per_page = 4 

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # PAGE 1: Grid View
        self.grid_container = QWidget()
        self.grid_main_layout = QHBoxLayout(self.grid_container)
        self.grid_layout = QGridLayout()
        self.grid_main_layout.addLayout(self.grid_layout, stretch=5)
        self._setup_sidebar()
        self.stack.addWidget(self.grid_container)

        # PAGE 2: Big Picture View
        self.big_picture_container = QWidget()
        self.big_layout = QVBoxLayout(self.big_picture_container)
        self.back_btn = QPushButton("← EXIT FULL SCREEN")
        self.back_btn.setStyleSheet("background: #444; color: white; padding: 10px; font-weight: bold; border: none;")
        self.back_btn.clicked.connect(self.exit_full_screen)
        
        self.full_screen_content = QVBoxLayout()
        self.big_layout.addWidget(self.back_btn)
        self.big_layout.addLayout(self.full_screen_content)
        self.stack.addWidget(self.big_picture_container)

    def _setup_sidebar(self):
        self.sidebar = QVBoxLayout()
        self.sidebar.setContentsMargins(10, 20, 10, 20)

        self.add_btn = QPushButton("+ ADD CAMERA")
        self.add_btn.setFixedHeight(50)
        self.add_btn.setStyleSheet("background: #0078d7; color: white; font-weight: bold; border-radius: 5px;")
        self.add_btn.clicked.connect(self.add_camera_workflow)

        self.page_info = QLabel("PAGE 1 / 1")
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        for btn in [self.prev_btn, self.next_btn]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("background: #333; color: white; border-radius: 20px; border: none;")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.nav_layout.addWidget(self.prev_btn)
        self.nav_layout.addWidget(self.next_btn)

        self.total_count = QLabel("0")
        self.total_count.setStyleSheet("font-size: 32px; font-weight: bold; color: #00ffcc;")
        self.total_count.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.sidebar.addWidget(self.add_btn)
        self.sidebar.addSpacing(20)
        self.sidebar.addWidget(QLabel("NAVIGATION", styleSheet="color: #888;"))
        self.sidebar.addWidget(self.page_info)
        self.sidebar.addLayout(self.nav_layout)
        self.sidebar.addStretch()
        self.sidebar.addWidget(QLabel("TOTAL PERSONS", styleSheet="color: #888; text-align: center;"))
        self.sidebar.addWidget(self.total_count)
        self.grid_main_layout.addLayout(self.sidebar, stretch=1)

    def add_camera_workflow(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Camera Feed", "", "Images (*.jpg *.png *.jpeg)")
        if not file_path: return

        templates = ["Channel 3", "Channel 4", "Channel 9", "Channel 12"]
        choice, ok = QInputDialog.getItem(self, "Select Template", "Choose Channel Template:", templates, 0, False)
        if not ok: return

        new_cam = CameraWidget(len(self.all_cameras) + 1)
        new_cam.delete_requested.connect(self.remove_camera)
        new_cam.mousePressEvent = lambda event: self.show_full_screen(new_cam)
        
        self.all_cameras.append(new_cam)
        new_cam.load_image(file_path, channel_key=choice)
        
        self.update_view()
        self._refresh_total()

    def update_view(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget: widget.setParent(None)

        start = self.current_page * self.max_per_page
        end = start + self.max_per_page
        for i, cam in enumerate(self.all_cameras[start:end]):
            self.grid_layout.addWidget(cam, i // 2, i % 2)

        total_pages = max(1, (len(self.all_cameras) + self.max_per_page - 1) // self.max_per_page)
        self.page_info.setText(f"PAGE {self.current_page + 1} / {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(end < len(self.all_cameras))

    def show_full_screen(self, cam_widget):
        self.current_active_cam = cam_widget
        cam_widget.set_full_screen(True)
        self.full_screen_content.addWidget(cam_widget)
        self.stack.setCurrentIndex(1)

    def exit_full_screen(self):
        if hasattr(self, 'current_active_cam'):
            self.current_active_cam.set_full_screen(False)
            self.full_screen_content.removeWidget(self.current_active_cam)
            self.stack.setCurrentIndex(0)
            self.update_view()

    def remove_camera(self, cam_widget):
        if cam_widget in self.all_cameras:
            self.all_cameras.remove(cam_widget)
            cam_widget.deleteLater()
            self.update_view()
            self._refresh_total()

    def next_page(self): self.current_page += 1; self.update_view()
    def prev_page(self): self.current_page -= 1; self.update_view()
    def _refresh_total(self):
        total = sum(getattr(cam, 'person_count', 0) for cam in self.all_cameras)
        self.total_count.setText(str(total))