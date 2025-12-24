# header/toolbar.py
from PyQt6.QtWidgets import QToolBar, QWidget, QSizePolicy
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtCore import QSize

class RecapToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setIconSize(QSize(24, 24))
        self.setMovable(False) # Không cho người dùng kéo thanh này đi chỗ khác
        
        # --- STYLE GIAO DIỆN ---
        self.setStyleSheet("""
            QToolBar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #3c3c3c;
                spacing: 12px; /* Khoảng cách giữa các nút */
                padding: 8px;
            }
            QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px;
                font-size: 14px; /* Kích thước Emoji */
            }
            QToolButton:hover {
                background-color: #3c3c3c;
                color: white;
            }
            QToolButton:pressed {
                background-color: #505050;
            }
        """)
        
        # --- KHỞI TẠO CÁC NÚT ---
        self.init_actions()

    def init_actions(self):
        # 1. Nhóm File
        self.action_new = self.add_custom_action("📄", "Dự án mới")
        self.action_save = self.add_custom_action("💾", "Lưu dự án")
        self.action_export = self.add_custom_action("📤", "Xuất CapCut")
        
        self.addSeparator() # Gạch dọc

        # 2. Nhóm Edit
        self.action_undo = self.add_custom_action("⬅️", "Hoàn tác")
        self.action_redo = self.add_custom_action("➡️", "Làm lại")
        
        self.addSeparator()

        # 3. Nhóm View & Tools
        self.action_menu = self.add_custom_action("☰", "Menu")
        self.action_zoom = self.add_custom_action("🔍", "Chế độ Zoom")
        self.action_open = self.add_custom_action("📂", "Mở thư mục")

        self.addSeparator()

        # 4. Nhóm Playback (Để căn sang phải nếu muốn)
        # spacer = QWidget()
        # spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # self.addWidget(spacer)

        self.action_play = self.add_custom_action("▶️", "Chạy thử")
        self.action_stop = self.add_custom_action("⏹️", "Dừng lại")

        self.action_menu = self.add_custom_action("☰", "Menu")
        self.action_zoom = self.add_custom_action("🔍", "Chế độ Zoom")
        
        # [THÊM DÒNG NÀY] Nút sắp xếp
        self.action_sort = self.add_custom_action("🔢", "Sắp xếp theo số (1-9)")
        
        self.action_open = self.add_custom_action("📂", "Mở thư mục")

    def add_custom_action(self, icon_text, tooltip):
        """Hàm hỗ trợ tạo nút nhanh"""
        action = QAction(icon_text, self)
        action.setToolTip(tooltip)
        self.addAction(action)
        return action