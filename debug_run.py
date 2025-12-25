# file: debug_run.py
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox

try:
    # Thử import và chạy main
    from main import MagaRecapClone
    
    app = QApplication(sys.argv)
    window = MagaRecapClone()
    window.show()
    sys.exit(app.exec())
    
except Exception as e:
    # Bắt lỗi và hiện thông báo
    error_msg = traceback.format_exc()
    print("--------------------------------------------------")
    print("LỖI CHI TIẾT:", error_msg)
    print("--------------------------------------------------")
    
    if not QApplication.instance():
        app = QApplication(sys.argv)
    
    QMessageBox.critical(None, "Phát hiện Lỗi", f"Lỗi xảy ra:\n{e}\n\nXem terminal để thấy chi tiết.")
    sys.exit(1)