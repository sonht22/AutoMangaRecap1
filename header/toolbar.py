from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt

class RecapToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)
        
        # --- NHÓM 1: FILE ---
        # 1. Mở Folder
        self.action_open = QAction("📂 Mở Folder Ảnh", self)
        self.action_open.setToolTip("Mở thư mục chứa ảnh truyện")
        self.addAction(self.action_open)
        
        # 2. Lưu Project [QUAN TRỌNG]
        self.action_save = QAction("💾 Lưu Project", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.setToolTip("Lưu lại tiến độ làm việc")
        self.addAction(self.action_save)

        # 3. Mở Project [QUAN TRỌNG]
        self.action_load_project = QAction("📂 Mở Project", self)
        self.action_load_project.setShortcut("Ctrl+O")
        self.action_load_project.setToolTip("Mở lại dự án cũ")
        self.addAction(self.action_load_project)
        
        self.addSeparator()
        
        # --- NHÓM 2: CÔNG CỤ ---
        self.action_sort = QAction("🔢 Sắp xếp", self)
        self.addAction(self.action_sort)
        
        self.addSeparator()
        
        # --- NHÓM 3: BẬT/TẮT PANEL ---
        self.action_toggle_cut = QAction("✂️ Panel Cắt", self)
        self.action_toggle_cut.setCheckable(True) 
        self.action_toggle_cut.setChecked(True)
        self.addAction(self.action_toggle_cut)
        
        self.action_toggle_trans = QAction("文 Panel Dịch", self)
        self.action_toggle_trans.setCheckable(True)
        self.action_toggle_trans.setChecked(False)
        self.addAction(self.action_toggle_trans)