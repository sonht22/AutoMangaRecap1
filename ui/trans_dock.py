# file: ui/trans_dock.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton, 
                             QLabel, QHBoxLayout, QDockWidget, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt

class TranslationDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Translation Tools", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- PHẦN 1: TRÍCH XUẤT VĂN BẢN (OCR) ---
        grp_ocr = QGroupBox("1. Trích Xuất Văn Bản (OCR)")
        ocr_layout = QVBoxLayout()
        
        # Chọn ngôn ngữ ảnh gốc
        row_lang = QHBoxLayout()
        row_lang.addWidget(QLabel("Ngôn ngữ ảnh:"))
        self.combo_src_lang = QComboBox()
        self.combo_src_lang.addItems(["Tiếng Nhật (Dọc)", "Tiếng Nhật (Ngang)", "Tiếng Hàn", "Tiếng Anh", "Tiếng Trung"])
        row_lang.addWidget(self.combo_src_lang)
        ocr_layout.addLayout(row_lang)
        
        # Nút chạy OCR
        self.btn_ocr = QPushButton("🔍 Quét Text (OCR)")
        self.btn_ocr.setStyleSheet("background-color: #005a9e; color: white; font-weight: bold; padding: 8px;")
        ocr_layout.addWidget(self.btn_ocr)
        
        grp_ocr.setLayout(ocr_layout)
        layout.addWidget(grp_ocr)
        
        # --- PHẦN 2: DỊCH THUẬT ---
        grp_trans = QGroupBox("2. Dịch Thuật")
        trans_layout = QVBoxLayout()
        
        # Chọn ngôn ngữ đích
        row_target = QHBoxLayout()
        row_target.addWidget(QLabel("Dịch sang:"))
        self.combo_target_lang = QComboBox()
        self.combo_target_lang.addItems(["Tiếng Việt", "Tiếng Anh", "Tiếng Hàn"])
        row_target.addWidget(self.combo_target_lang)
        trans_layout.addLayout(row_target)
        
        # Tùy chọn dịch
        self.chk_auto_fill = QCheckBox("Tự điền vào bảng")
        self.chk_auto_fill.setChecked(True)
        trans_layout.addWidget(self.chk_auto_fill)
        
        # Nút Dịch
        self.btn_translate = QPushButton("🌐 Dịch Ngay")
        self.btn_translate.setStyleSheet("background-color: #006600; color: white; font-weight: bold; padding: 8px;")
        trans_layout.addWidget(self.btn_translate)
        
        grp_trans.setLayout(trans_layout)
        layout.addWidget(grp_trans)
        
        # --- STATUS ---
        self.lbl_status = QLabel("Trạng thái: Sẵn sàng")
        self.lbl_status.setStyleSheet("color: gray; font-style: italic; margin-top: 10px;")
        layout.addWidget(self.lbl_status)
        
        self.setWidget(container)