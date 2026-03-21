import sys
from PyQt6.QtWidgets import QApplication
from cctv_manager import CCTVManager


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CCTVManager()
    window.show()
    sys.exit(app.exec())
