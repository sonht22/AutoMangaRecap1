import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                             QSplitter, QHeaderView)
from PyQt6.QtCore import Qt

# --- IMPORT CÁC MODULE GIAO DIỆN & LOGIC ---
from header.toolbar import RecapToolbar       # Thanh công cụ bên trên
from ui.zoom_viewer import PhotoViewer        # Khung xem ảnh ở giữa
from ui.drag_list import DraggableListWidget  # Danh sách ảnh bên trái
from ui.panel_dock import PanelDock           # [MỚI] Bảng điều khiển cắt ảnh bên phải
from ui.app_logic import AppLogic             # Bộ não xử lý logic

class MagaRecapClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Manga Recap (Full Features)")
        self.resize(1400, 850) # Mở rộng cửa sổ ra một chút

        # ==================================================
        # 1. KHỞI TẠO LOGIC (BỘ NÃO)
        # ==================================================
        # Phải khởi tạo cái này đầu tiên để các nút bấm có chỗ gọi đến
        self.logic = AppLogic(self) 

        # ==================================================
        # 2. GIAO DIỆN: TOOLBAR (THANH CÔNG CỤ TRÊN CÙNG)
        # ==================================================
        self.toolbar = RecapToolbar(self)
        self.addToolBar(self.toolbar)
        
        # --- Kết nối các nút trên Toolbar với Logic ---
        # Nút Mở folder
        if hasattr(self.toolbar, 'action_open'):
             self.toolbar.action_open.triggered.connect(self.logic.action_load_folder)
        
        # Nút Cắt ảnh (Hình cái kéo)
        if hasattr(self.toolbar, 'action_cut'):
             self.toolbar.action_cut.triggered.connect(self.logic.action_smart_cut)

        # Nút Sắp xếp (Hình số 123)
        if hasattr(self.toolbar, 'action_sort'):
             self.toolbar.action_sort.triggered.connect(self.logic.action_auto_sort)

        # ==================================================
        # 3. GIAO DIỆN: DOCK WIDGET (BẢNG CẮT ẢNH BÊN PHẢI)
        # ==================================================
        self.panel_dock = PanelDock(self)
        # Gắn nó vào mép phải màn hình
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.panel_dock)
        
        # Kết nối nút "Cut Panels" trong Dock với Logic
        self.panel_dock.btn_cut_trigger.clicked.connect(self.logic.action_smart_cut)

        # ==================================================
        # 4. GIAO DIỆN: KHUNG CHÍNH (CENTER)
        # ==================================================
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- A. CỘT TRÁI (DANH SÁCH ẢNH) ---
        left_layout = QVBoxLayout()
        
        # Nút chọn folder (Dự phòng nếu không dùng Toolbar)
        self.btn_load_folder = QPushButton("📂 Chọn Folder")
        self.btn_load_folder.setStyleSheet("""
            QPushButton {
                padding: 10px; background-color: #0078D7; color: white; 
                font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #0063b1; }
        """)
        self.btn_load_folder.clicked.connect(self.logic.action_load_folder)
        
        # Danh sách (List Widget)
        self.image_list = DraggableListWidget()
        # Kết nối sự kiện
        self.image_list.currentRowChanged.connect(self.logic.display_image)    # Click xem ảnh
        self.image_list.orderChanged.connect(self.logic.sync_table_order)      # Kéo thả/Xóa -> Cập nhật bảng
        self.image_list.itemChanged.connect(self.logic.handle_rename_file)     # Đổi tên -> Cập nhật file thật
        
        left_layout.addWidget(self.btn_load_folder)
        left_layout.addWidget(QLabel("Danh sách (Sửa tên = Đổi file thật):"))
        left_layout.addWidget(self.image_list)

        # --- B. CỘT GIỮA (TRÌNH XEM ẢNH) ---
        self.viewer = PhotoViewer(self)

        # --- C. CỘT PHẢI (BẢNG KỊCH BẢN 6 CỘT) ---
        right_layout = QVBoxLayout()
        self.btn_analyze = QPushButton("✨ Phân tích AI (Coming Soon)")
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                padding: 10px; background-color: #8A2BE2; color: white; 
                font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #7209b7; }
        """)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6) # 6 Cột đầy đủ
        self.table.setHorizontalHeaderLabels([
            "ID", 
            "File Ảnh", 
            "Văn bản (OCR)", 
            "Dịch (VN)", 
            "Kịch Bản (Recap)", 
            "Audio"
        ])
        
        # Cấu hình độ rộng cột
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # File Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # OCR
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Dịch
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Recap
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   # Audio
        self.table.setColumnWidth(5, 50)
        
        right_layout.addWidget(self.btn_analyze)
        right_layout.addWidget(self.table)

        # --- D. PHÂN CHIA (SPLITTER) ---
        # Giúp người dùng kéo qua lại kích thước các cột
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)  # Cột trái
        splitter.addWidget(self.viewer)  # Cột giữa
        splitter.addWidget(right_widget) # Cột phải
        
        # Tỷ lệ mặc định: Trái 200, Giữa 600, Phải 450
        splitter.setSizes([200, 600, 450])

        main_layout.addWidget(splitter)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        
        # Thiết lập Font chữ hệ thống cho đẹp
        font = app.font()
        font.setPointSize(10) # Cỡ chữ 10 cho dễ nhìn
        app.setFont(font)
        
        window = MagaRecapClone()
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        sys.exit()