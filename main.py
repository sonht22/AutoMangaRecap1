import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                             QSplitter, QHeaderView, QListWidget)
from PyQt6.QtCore import Qt

# Cấu hình đường dẫn
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import module (kèm xử lý lỗi nếu thiếu file)
try:
    from header.toolbar import RecapToolbar       
    from ui.drag_list import DraggableListWidget  
    from ui.custom_delegate import MultiLineDelegate 
except ImportError:
    RecapToolbar = None
    DraggableListWidget = None
    MultiLineDelegate = None

from ui.zoom_viewer import PhotoViewer        
from ui.panel_dock import PanelDock           
from ui.trans_dock import TranslationDock
from ui.app_logic import AppLogic             

class MagaRecapClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Manga Recap - Pro Editor (PyQt6)")
        self.resize(1400, 850)
        
        # --- 1. KHỞI TẠO GIAO DIỆN (UI) ---
        
        # A. Toolbar
        if RecapToolbar:
            self.toolbar = RecapToolbar(self)
            self.addToolBar(self.toolbar)

        # B. Dock Widgets (Bảng bên phải)
        self.panel_dock = PanelDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.panel_dock)
        
        self.trans_dock = TranslationDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.trans_dock)
        self.trans_dock.setVisible(False) 
        
        self.tabifyDockWidget(self.panel_dock, self.trans_dock)

        # C. Khu vực chính (Center)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Cột Trái: Danh sách ảnh
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

        # Cột Giữa: Viewer ảnh
        self.viewer = PhotoViewer(self)

        # Cột Phải: Bảng kết quả (Table)
        right_layout = QVBoxLayout()
        self.btn_analyze = QPushButton("✨ Phân tích AI (Coming Soon)")
        self.btn_analyze.setStyleSheet("background-color: #8A2BE2; color: white; padding: 6px; font-weight: bold;")
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "File Ảnh", "OCR Text", "Translation"])
        self.table.setColumnHidden(1, True) # Ẩn cột dịch tạm thời
        self.table.setWordWrap(True)
        
        # Cấu hình Bảng Pro (Excel Style)
        if MultiLineDelegate:
            delegate = MultiLineDelegate(self.table)
            self.table.setItemDelegateForColumn(2, delegate) # Cột OCR
            # --- [MỚI] Áp dụng luôn cho cột Translation (Cột 3) ---
            self.table.setItemDelegateForColumn(3, delegate)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | 
                                   QTableWidget.EditTrigger.AnyKeyPressed |
                                   QTableWidget.EditTrigger.SelectedClicked)
        
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #d0d0d0; font-size: 11pt; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #0078D7; color: white; }
            QTableWidget::item:selected:active { background-color: white; color: black; }
        """)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        right_layout.addWidget(self.btn_analyze)
        right_layout.addWidget(self.table)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Splitter (Thanh chia cột)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.viewer)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750, 400])
        main_layout.addWidget(splitter)

        # --- 2. KHỞI TẠO LOGIC VÀ KẾT NỐI ---
        self.logic = AppLogic(self)
        
        # Kết nối nút cơ bản
        self.btn_load_folder.clicked.connect(self.logic.action_load_folder)
        self.image_list.currentRowChanged.connect(self.logic.display_image)

        # --- [QUAN TRỌNG] KẾT NỐI TOOLBAR ---
        if hasattr(self, 'toolbar'):
            # 1. Nút Mở Folder
            if hasattr(self.toolbar, 'action_open'):
                self.toolbar.action_open.triggered.connect(self.logic.action_load_folder)

            # 2. Nút Lưu Project
            if hasattr(self.toolbar, 'action_save'):
                self.toolbar.action_save.triggered.connect(self.logic.save_project)

            # 3. Nút Mở Project
            if hasattr(self.toolbar, 'action_load_project'):
                self.toolbar.action_load_project.triggered.connect(self.logic.load_project)
            
            # 4. Nút Sắp xếp
            if hasattr(self.toolbar, 'action_sort'):
                self.toolbar.action_sort.triggered.connect(self.logic.action_auto_sort)

            # 5. Các nút Bật/Tắt Panel
            if hasattr(self.toolbar, 'action_toggle_cut'):
                self.toolbar.action_toggle_cut.triggered.connect(self.toggle_cut_panel)
                self.panel_dock.visibilityChanged.connect(self.toolbar.action_toggle_cut.setChecked)
            
            if hasattr(self.toolbar, 'action_toggle_trans'):
                self.toolbar.action_toggle_trans.triggered.connect(self.toggle_trans_panel)
                self.trans_dock.visibilityChanged.connect(self.toolbar.action_toggle_trans.setChecked)

    # Hàm chuyển đổi Panel
    def toggle_cut_panel(self, checked):
        self.panel_dock.setVisible(checked)
        if checked: 
            self.trans_dock.setVisible(False)
            # Tắt chế độ vẽ nếu đang bật để tránh lỗi
            self.viewer.reset_mode()

    def toggle_trans_panel(self, checked):
        self.trans_dock.setVisible(checked)
        if checked: 
            self.panel_dock.setVisible(False)
            self.viewer.reset_mode()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MagaRecapClone()
    window.show()
    sys.exit(app.exec())