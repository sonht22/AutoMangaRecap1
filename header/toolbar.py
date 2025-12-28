from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class RecapToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setMovable(False)
        
        # --- NHÓM 1: FILE ---
        
        # 1. Nút Mở Folder Ảnh
        self.action_open = QAction("📂 Mở Folder Ảnh", self)
        self.action_open.setToolTip("Mở thư mục chứa ảnh truyện")
        self.addAction(self.action_open)
        
        # 2. Nút Lưu (Lưu nhanh vào file hiện tại)
        self.action_save = QAction("💾 Lưu", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.setToolTip("Lưu lại tiến độ (Ghi đè file cũ)")
        self.addAction(self.action_save)

        # 3. Nút Lưu Mới (Save As - Lưu ra file khác)
        self.action_save_as = QAction("💾 Lưu Mới...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.setToolTip("Lưu ra file dự án mới")
        self.addAction(self.action_save_as)

        # 4. Nút Mở Project (Cái bạn đang bị thiếu)
        self.action_load_project = QAction("📂 Mở Project", self)
        self.action_load_project.setShortcut("Ctrl+O")
        self.action_load_project.setToolTip("Mở lại dự án cũ (.json)")
        self.addAction(self.action_load_project) # <--- Dòng này quan trọng!
        
        self.addSeparator()
        
        # --- NHÓM 2: CÔNG CỤ ---
        
        # 5. Nút Sắp xếp
        self.action_sort = QAction("🔢 Sắp xếp", self)
        self.addAction(self.action_sort)
        
        self.addSeparator()
        
        # --- NHÓM 3: BẬT/TẮT PANEL ---
        
        # 6. Panel Cắt
        self.action_toggle_cut = QAction("✂️ Panel Cắt", self)
        self.action_toggle_cut.setCheckable(True) 
        self.action_toggle_cut.setChecked(True)
        self.addAction(self.action_toggle_cut)
        
        # 7. Panel Dịch
        self.action_toggle_trans = QAction("文 Panel Dịch", self)
        self.action_toggle_trans.setCheckable(True)
        self.action_toggle_trans.setChecked(False)
        self.addAction(self.action_toggle_trans)