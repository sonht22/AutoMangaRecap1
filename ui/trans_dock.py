from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QPushButton, 
                             QLabel, QHBoxLayout, QDockWidget, QComboBox, 
                             QCheckBox, QLineEdit, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt

class TranslationDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Translation & Voice Tools", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- 1. OCR ---
        grp_ocr = QGroupBox("1. Trích Xuất Văn Bản (OCR)")
        ocr_layout = QVBoxLayout()
        row_lang = QHBoxLayout()
        row_lang.addWidget(QLabel("Ngôn ngữ ảnh:"))
        self.combo_src_lang = QComboBox()
        self.combo_src_lang.addItems(["Tiếng Nhật (Dọc)", "Tiếng Nhật (Ngang)", "Tiếng Hàn", "Tiếng Anh", "Tiếng Trung"])
        row_lang.addWidget(self.combo_src_lang)
        ocr_layout.addLayout(row_lang)
        self.btn_ocr = QPushButton("🔍 Quét Text (OCR)")
        self.btn_ocr.setStyleSheet("background-color: #005a9e; color: white; font-weight: bold; padding: 6px;")
        ocr_layout.addWidget(self.btn_ocr)
        grp_ocr.setLayout(ocr_layout)
        layout.addWidget(grp_ocr)
        
        # --- 2. DỊCH ---
        grp_trans = QGroupBox("2. Dịch Thuật")
        trans_layout = QVBoxLayout()
        row_target = QHBoxLayout()
        row_target.addWidget(QLabel("Dịch sang:"))
        self.combo_target_lang = QComboBox()
        self.combo_target_lang.addItems(["Tiếng Việt", "Tiếng Anh", "Tiếng Hàn"])
        row_target.addWidget(self.combo_target_lang)
        trans_layout.addLayout(row_target)
        self.chk_auto_fill = QCheckBox("Tự điền vào bảng")
        self.chk_auto_fill.setChecked(True)
        trans_layout.addWidget(self.chk_auto_fill)
        self.btn_translate = QPushButton("🌐 Dịch Ngay")
        self.btn_translate.setStyleSheet("background-color: #006600; color: white; font-weight: bold; padding: 6px;")
        trans_layout.addWidget(self.btn_translate)
        grp_trans.setLayout(trans_layout)
        layout.addWidget(grp_trans)

        # --- 3. VOICE (TTS) ---
        grp_voice = QGroupBox("3. Tạo Giọng Nói (AI TTS)")
        voice_layout = QVBoxLayout()
        
        # Nhập API Key
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("Dán API Key (sk_...) vào đây")
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        voice_layout.addWidget(self.txt_api_key)

        # Chọn Provider & Model
        row_provider = QHBoxLayout()
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["Minimax", "ElevenLabs"]) # Đưa Minimax lên đầu
        row_provider.addWidget(self.combo_provider)
        
        self.combo_model = QComboBox()
        # [QUAN TRỌNG] Cập nhật list model chuẩn
        self.combo_model.addItems(["speech-01-turbo", "speech-01-hd", "speech-01-hd-2.5", "eleven_multilingual_v2"])
        self.combo_model.setEditable(True)
        row_provider.addWidget(self.combo_model)
        voice_layout.addLayout(row_provider)

        # Chọn giọng (Voice ID) + Nút Thêm
        row_voice = QHBoxLayout()
        self.combo_voice = QComboBox()
        self.combo_voice.setEditable(True) 
        self.combo_voice.setPlaceholderText("Chọn hoặc dán Voice ID...")
        # Thêm mẫu
        self.combo_voice.addItem("Mẫu Minimax (Nam)", "209533299589184")
        
        row_voice.addWidget(self.combo_voice)
        
        # Nút Thêm Giọng Mới
        self.btn_add_voice = QPushButton("➕")
        self.btn_add_voice.setToolTip("Lưu giọng mới vào danh sách")
        self.btn_add_voice.setFixedWidth(30)
        self.btn_add_voice.clicked.connect(self.add_custom_voice)
        row_voice.addWidget(self.btn_add_voice)
        
        voice_layout.addLayout(row_voice)

        # Nút tạo Audio
        self.btn_tts = QPushButton("🎙️ Tạo Audio (TTS)")
        self.btn_tts.setStyleSheet("background-color: #D35400; color: white; font-weight: bold; padding: 6px;")
        voice_layout.addWidget(self.btn_tts)
        
        grp_voice.setLayout(voice_layout)
        layout.addWidget(grp_voice)
        
        self.setWidget(container)

    def add_custom_voice(self):
        """Hộp thoại để người dùng tự thêm tên giọng"""
        current_text = self.combo_voice.currentText().strip()
        
        # Bước 1: Nhập ID (Mặc định lấy cái đang nhập trong ô)
        voice_id, ok1 = QInputDialog.getText(self, "Thêm Giọng Mới", "Nhập Voice ID (Mã số):", text=current_text)
        if not ok1 or not voice_id: return
        
        # Bước 2: Nhập Tên
        voice_name, ok2 = QInputDialog.getText(self, "Thêm Giọng Mới", "Đặt tên gợi nhớ (VD: Giọng Nam Trầm):")
        if not ok2 or not voice_name: return
        
        # Thêm vào ComboBox
        display_text = f"{voice_name} ({voice_id})"
        self.combo_voice.addItem(display_text, voice_id)
        
        # Chọn luôn cái mới thêm
        index = self.combo_voice.findText(display_text)
        if index >= 0: self.combo_voice.setCurrentIndex(index)