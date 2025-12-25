import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                             QSplitter, QHeaderView, QListWidget)
from PyQt6.QtCore import Qt

# --- CẤU HÌNH ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# --- IMPORT MODULE ---
try:
    from header.toolbar import RecapToolbar       
    from ui.drag_list import DraggableListWidget  
except ImportError:
    RecapToolbar = None
    DraggableListWidget = None
    print("Cảnh báo: Thiếu module giao diện cũ.")

from ui.zoom_viewer import PhotoViewer        
from ui.panel_dock import PanelDock           
from ui.app_logic import AppLogic             

class MagaRecapClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Manga Recap - Pro Editor")
        self.resize(1400, 850)
        
        # 1. KHỞI TẠO UI
        
        # --- Toolbar ---
        if RecapToolbar:
            self.toolbar = RecapToolbar(self)
            self.addToolBar(self.toolbar)

        # --- Dock Widget (Bảng Cắt) ---
        self.panel_dock = PanelDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.panel_dock)

        # --- Center Widget ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Cột Trái
        left_layout = QVBoxLayout()
        self.btn_load_folder = QPushButton("📂 Chọn Folder")
        self.btn_load_folder.setStyleSheet("background-color: #0078D7; color: white; padding: 6px; font-weight: bold;")
        self.lbl_list = QLabel("Danh sách file gốc:")
        
        if DraggableListWidget: self.image_list = DraggableListWidget()
        else: self.image_list = QListWidget()
            
        left_layout.addWidget(self.btn_load_folder)
        left_layout.addWidget(self.lbl_list)
        left_layout.addWidget(self.image_list)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # Cột Giữa (Viewer)
        self.viewer = PhotoViewer(self)

        # Cột Phải (Bảng AI)
        right_layout = QVBoxLayout()
        self.btn_analyze = QPushButton("✨ Phân tích AI (Coming Soon)")
        self.btn_analyze.setStyleSheet("background-color: #8A2BE2; color: white; padding: 6px; font-weight: bold;")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "File Ảnh", "OCR Text", "Translation"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        right_layout.addWidget(self.btn_analyze)
        right_layout.addWidget(self.table)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.viewer)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750, 400])
        main_layout.addWidget(splitter)

        # 2. KHỞI TẠO LOGIC
        self.logic = AppLogic(self)
        
        # Kết nối cơ bản
        self.btn_load_folder.clicked.connect(self.logic.action_load_folder)
        self.image_list.currentRowChanged.connect(self.logic.display_image)

        # --- [MỚI] KẾT NỐI TOOLBAR ĐỂ BẬT/TẮT DOCK ---
        if hasattr(self, 'toolbar') and hasattr(self.toolbar, 'action_toggle_cut'):
            # 1. Bấm nút Toolbar -> Ẩn/Hiện Dock
            self.toolbar.action_toggle_cut.triggered.connect(self.toggle_cut_panel)
            
            # 2. Đóng Dock bằng dấu X -> Nút Toolbar tự tắt theo (Đồng bộ)
            self.panel_dock.visibilityChanged.connect(self.toolbar.action_toggle_cut.setChecked)

    def toggle_cut_panel(self, checked):
        """Hàm xử lý Bật/Tắt panel cắt"""
        self.panel_dock.setVisible(checked)
        if not checked:
            # Nếu tắt panel, ta nên thoát chế độ vẽ khung để tránh bấm nhầm
            self.viewer.reset_mode()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    window = MagaRecapClone()
    window.show()
    sys.exit(app.exec())