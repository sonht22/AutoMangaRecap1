# file: ui/panel_dock.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QSpinBox, 
                             QPushButton, QRadioButton, QLabel, QHBoxLayout, QDockWidget)
from PyQt6.QtCore import Qt

class PanelDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Panel Operations", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- 1. SETTINGS QUÉT ---
        grp_detect = QGroupBox("1. Panel Detection")
        detect_layout = QVBoxLayout()
        
        # Nút Scan
        self.btn_scan = QPushButton("🔍 Auto Scan (Quét Ảnh)")
        self.btn_scan.setStyleSheet("background-color: #006666; color: white; padding: 6px; font-weight: bold;")
        detect_layout.addWidget(self.btn_scan)
        
        # Điều chỉnh kích thước
        row_adj = QHBoxLayout()
        self.spin_w = QSpinBox()
        self.spin_w.setRange(-500, 500)
        self.spin_w.setSuffix(" px (Rộng)")
        self.spin_h = QSpinBox()
        self.spin_h.setRange(-500, 500)
        self.spin_h.setSuffix(" px (Cao)")
        
        row_adj.addWidget(self.spin_w)
        row_adj.addWidget(self.spin_h)
        detect_layout.addLayout(row_adj)
        
        grp_detect.setLayout(detect_layout)
        layout.addWidget(grp_detect)
        
        # --- 2. CÔNG CỤ CHỈNH SỬA (CẬP NHẬT) ---
        grp_tools = QGroupBox("2. Manual Tools")
        tools_layout = QVBoxLayout() # Đổi sang xếp dọc cho đẹp
        
        # Hàng 1: Thêm và Xóa đã chọn
        row_tools_1 = QHBoxLayout()
        self.btn_add = QPushButton("➕ Thêm khung")
        self.btn_del = QPushButton("🗑️ Xóa khung đã chọn") # <--- Đổi tên nút này
        
        row_tools_1.addWidget(self.btn_add)
        row_tools_1.addWidget(self.btn_del)
        
        # Hàng 2: Xóa tất cả (Nút mới)
        self.btn_clear_all = QPushButton("🧹 Xóa tất cả (Làm mới)")
        self.btn_clear_all.setStyleSheet("background-color: #552200; color: #ffcccc;")
        
        tools_layout.addLayout(row_tools_1)
        tools_layout.addWidget(self.btn_clear_all) # <--- Thêm nút xóa tất cả
        
        grp_tools.setLayout(tools_layout)
        layout.addWidget(grp_tools)
        
        # --- 3. CÀI ĐẶT CẮT ---
        grp_cut = QGroupBox("3. Cutting Settings")
        cut_layout = QVBoxLayout()
        
        self.radio_top = QRadioButton("Top to Bottom (Dọc)")
        self.radio_top.setChecked(True)
        self.radio_left = QRadioButton("Left to Right (Ngang)")
        
        cut_layout.addWidget(self.radio_top)
        cut_layout.addWidget(self.radio_left)
        grp_cut.setLayout(cut_layout)
        layout.addWidget(grp_cut)
        
        # --- 4. NÚT CẮT LỚN ---
        self.btn_cut_trigger = QPushButton("✂️ Cut Panels & Save")
        self.btn_cut_trigger.setFixedHeight(50)
        self.btn_cut_trigger.setStyleSheet("""
            QPushButton { 
                background-color: #333; color: white; 
                border: 2px solid #555; font-weight: bold; font-size: 14px; 
            }
            QPushButton:hover { background-color: #cc0000; border-color: red; }
        """)
        layout.addWidget(self.btn_cut_trigger)
        
        self.setWidget(container)