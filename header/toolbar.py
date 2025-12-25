# file: header/toolbar.py
from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt

class RecapToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setMovable(False) # Cố định toolbar cho gọn
        
        # --- 1. Action Mở Folder ---
        self.action_open = QAction("📂 Mở Folder", self)
        self.addAction(self.action_open)
        
        # --- 2. Action Sắp xếp ---
        self.action_sort = QAction("🔢 Sắp xếp", self)
        self.addAction(self.action_sort)
        
        self.addSeparator() # Vạch ngăn cách
        
        # --- 3. [MỚI] Action Bật/Tắt Panel Cắt ---
        # setCheckable(True) giúp nút này hoạt động như công tắc đèn (Bấm lún xuống / Nảy lên)
        self.action_toggle_cut = QAction("✂️ Panel Cắt", self)
        self.action_toggle_cut.setCheckable(True) 
        self.action_toggle_cut.setChecked(True) # Mặc định là Đang Bật
        self.action_toggle_cut.setToolTip("Bật/Tắt khung công cụ cắt ảnh bên phải")
        self.addAction(self.action_toggle_cut)