import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                             QSplitter, QHeaderView, QListWidget, QMessageBox, 
                             QTableWidgetItem, QInputDialog)
from PyQt6.QtCore import Qt
from dotenv import load_dotenv  # Thư viện đọc file .env

# --- CẤU HÌNH PATH & IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load biến môi trường từ file .env
load_dotenv()

# --- SỬA ĐOẠN IMPORT NÀY ĐỂ DEBUG ---
import traceback # Thêm thư viện này để soi lỗi

try:
    from AI.gemini_worker import GeminiScriptGenerator
    print("✅ Đã load thành công module AI/gemini_worker")
except Exception as e:
    GeminiScriptGenerator = None
    print("\n" + "="*40)
    print("❌ LỖI NGHIÊM TRỌNG KHI IMPORT AI:")
    print(e) # In ra lỗi cụ thể (Ví dụ: No module named 'google')
    print("-" * 40)
    traceback.print_exc() # In ra dòng code bị lỗi
    print("="*40 + "\n")

# Import các module giao diện cũ của bạn
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
        self.setWindowTitle("Auto Manga Recap - Pro Editor (PyQt6 + Gemini AI)")
        self.resize(1400, 850)
        
        # --- ĐỊNH NGHĨA CỘT BẢNG ---
        self.COL_ID = 0
        self.COL_FILE = 1      # Tên file ảnh (Ẩn)
        self.COL_OCR = 2       # Text gốc từ ảnh
        self.COL_TRANS = 3     # Bản dịch thô
        self.COL_SCRIPT = 4    # [MỚI] Kịch bản AI viết
        self.COL_VOI = 5       # Đường dẫn file âm thanh

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

        # --- CỘT TRÁI: DANH SÁCH ẢNH ---
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

        # --- CỘT GIỮA: VIEWER ẢNH ---
        self.viewer = PhotoViewer(self)

        # --- CỘT PHẢI: BẢNG KẾT QUẢ & NÚT ---
        right_layout = QVBoxLayout()
        
        # Layout cho các nút chức năng
        btn_tools_layout = QHBoxLayout()
        
        self.btn_ocr = QPushButton("🔍 Scan Text (OCR)")
        self.btn_ocr.setStyleSheet("padding: 6px;")
        
        # [MỚI] Nút Tạo Kịch Bản
        self.btn_gen_script = QPushButton("✨ Tạo Kịch Bản (Gemini)")
        self.btn_gen_script.setStyleSheet("background-color: #8A2BE2; color: white; padding: 6px; font-weight: bold;")
        self.btn_gen_script.setToolTip("Dùng AI viết lại lời thoại thành văn kể chuyện")

        btn_tools_layout.addWidget(self.btn_ocr)
        btn_tools_layout.addWidget(self.btn_gen_script)
        
        # Cấu hình Bảng (Table) - 6 Cột
        self.table = QTableWidget(0, 6)
        headers = ["ID", "File Ảnh", "OCR Text", "Translation", "Kịch bản (AI)", "VOI"]
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setColumnHidden(self.COL_FILE, True) # Ẩn cột tên file cho gọn
        self.table.setWordWrap(True)
        
        # Cấu hình Delegate (Cho phép xuống dòng khi edit)
        if MultiLineDelegate:
            delegate = MultiLineDelegate(self.table)
            self.table.setItemDelegateForColumn(self.COL_OCR, delegate)
            self.table.setItemDelegateForColumn(self.COL_TRANS, delegate)
            self.table.setItemDelegateForColumn(self.COL_SCRIPT, delegate) # Áp dụng cho cột Kịch bản
        
        # Các cài đặt bảng
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | 
                                   QTableWidget.EditTrigger.AnyKeyPressed |
                                   QTableWidget.EditTrigger.SelectedClicked)
        
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #d0d0d0; font-size: 11pt; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #0078D7; color: white; }
        """)
        
        # Resize cột
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_OCR, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_TRANS, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_SCRIPT, QHeaderView.ResizeMode.Stretch) # Kịch bản rộng ra
        header.setSectionResizeMode(self.COL_VOI, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        right_layout.addLayout(btn_tools_layout)
        right_layout.addWidget(self.table)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Splitter (Thanh chia cột co giãn)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.viewer)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750, 450])
        main_layout.addWidget(splitter)

        # --- 2. KHỞI TẠO LOGIC VÀ KẾT NỐI ---
        self.logic = AppLogic(self)
        
        # Kết nối sự kiện cơ bản
        self.btn_load_folder.clicked.connect(self.logic.action_load_folder)
        self.image_list.currentRowChanged.connect(self.logic.display_image)
        
        # [MỚI] Kết nối nút Gemini
        self.btn_gen_script.clicked.connect(self.start_gemini_script)

        # Kết nối Toolbar (Giữ nguyên code cũ)
        if hasattr(self, 'toolbar'):
            if hasattr(self.toolbar, 'action_open'):
                self.toolbar.action_open.triggered.connect(self.logic.action_load_folder)
            if hasattr(self.toolbar, 'action_save'):
                self.toolbar.action_save.triggered.connect(self.logic.save_project)
            if hasattr(self.toolbar, 'action_save_as'):
                self.toolbar.action_save_as.triggered.connect(self.logic.save_project_as)
            if hasattr(self.toolbar, 'action_load_project'):
                self.toolbar.action_load_project.triggered.connect(self.logic.load_project)
            if hasattr(self.toolbar, 'action_sort'):
                self.toolbar.action_sort.triggered.connect(self.logic.action_auto_sort)
            if hasattr(self.toolbar, 'action_toggle_cut'):
                self.toolbar.action_toggle_cut.triggered.connect(self.toggle_cut_panel)
                self.panel_dock.visibilityChanged.connect(self.toolbar.action_toggle_cut.setChecked)
            if hasattr(self.toolbar, 'action_toggle_trans'):
                self.toolbar.action_toggle_trans.triggered.connect(self.toggle_trans_panel)
                self.trans_dock.visibilityChanged.connect(self.toolbar.action_toggle_trans.setChecked)

    # --- HELPER UI ---
    def toggle_cut_panel(self, checked):
        self.panel_dock.setVisible(checked)
        if checked: 
            self.trans_dock.setVisible(False)
            self.viewer.reset_mode()

    def toggle_trans_panel(self, checked):
        self.trans_dock.setVisible(checked)
        if checked: 
            self.panel_dock.setVisible(False)
            self.viewer.reset_mode()

    # --- [CHỨC NĂNG AI] ---
    def start_gemini_script(self):
        """
        Hàm xử lý khi bấm nút 'Tạo Kịch Bản'.
        Quy trình:
        1. Kiểm tra Module & API Key.
        2. Gom dữ liệu text từ bảng.
        3. Hỏi người dùng phong cách viết (Hài hước, nghiêm túc...).
        4. Gửi cho AI xử lý.
        """
        
        # --- BƯỚC 1: KIỂM TRA ĐIỀU KIỆN ---
        if not GeminiScriptGenerator:
            QMessageBox.critical(self, "Lỗi Module", "Không tìm thấy file 'AI/gemini_worker.py'.\nHãy kiểm tra lại thư mục dự án.")
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            QMessageBox.warning(self, "Thiếu API Key", 
                                "Chưa tìm thấy 'GEMINI_API_KEY' trong file .env!\n"
                                "Vui lòng kiểm tra lại file .env.")
            return

        # --- BƯỚC 2: THU THẬP DỮ LIỆU TỪ BẢNG ---
        data_to_process = []
        row_count = self.table.rowCount()
        
        for row in range(row_count):
            # Ưu tiên lấy cột Translation (Cột 3)
            item_trans = self.table.item(row, self.COL_TRANS)
            # Nếu không có dịch thì lấy cột OCR (Cột 2)
            item_ocr = self.table.item(row, self.COL_OCR)
            
            text_input = ""
            if item_trans and item_trans.text().strip():
                text_input = item_trans.text()
            elif item_ocr and item_ocr.text().strip():
                text_input = item_ocr.text()
            
            # Chỉ thêm vào danh sách nếu dòng đó có chữ
            if text_input:
                data_to_process.append((row, text_input))

        if not data_to_process:
            QMessageBox.information(self, "Trống", "Không tìm thấy nội dung (OCR hoặc Translation) để viết kịch bản.")
            return

        # --- BƯỚC 3: HỎI NGƯỜI DÙNG PHONG CÁCH (CUSTOM PROMPT) ---
        # Hộp thoại hiện ra để bạn nhập yêu cầu
        custom_style, ok = QInputDialog.getText(
            self, 
            "Cấu hình AI", 
            "Nhập phong cách kể chuyện bạn muốn:\n(Ví dụ: Hài hước, GenZ, Kịch tính, Review phim...)\nĐể trống sẽ dùng mặc định."
        )

        # Nếu người dùng bấm Cancel (Hủy) hoặc đóng hộp thoại -> Dừng lại
        if not ok:
            return

        # --- BƯỚC 4: KHỞI CHẠY LUỒNG AI (THREAD) ---
        
        # Khóa nút bấm để tránh spam
        self.btn_gen_script.setEnabled(False)
        self.btn_gen_script.setText("⏳ Đang viết kịch bản...")
        
        # Khởi tạo Worker, truyền Key, Dữ liệu và Style vào
        self.ai_thread = GeminiScriptGenerator(api_key, data_to_process, custom_style)
        
        # Kết nối các tín hiệu (Signal)
        self.ai_thread.update_signal.connect(self.update_script_cell)   # Cập nhật từng dòng
        self.ai_thread.finished_signal.connect(self.on_script_finished) # Khi xong hết
        self.ai_thread.error_signal.connect(self.on_script_error)       # Khi lỗi
        
        # Bắt đầu chạy
        self.ai_thread.start()
    def update_script_cell(self, row, text):
        """AI viết xong 1 dòng -> Cập nhật vào bảng ngay"""
        item = QTableWidgetItem(text)
        self.table.setItem(row, self.COL_SCRIPT, item)
        self.table.scrollToItem(item) # Cuộn tới dòng đang viết

    def on_script_finished(self):
        """Hoàn tất toàn bộ"""
        self.btn_gen_script.setEnabled(True)
        self.btn_gen_script.setText("✨ Tạo Kịch Bản (Gemini)")
        QMessageBox.information(self, "Thành công", "Đã tạo kịch bản xong!")

    def on_script_error(self, err_msg):
        """Gặp lỗi nghiêm trọng"""
        self.btn_gen_script.setEnabled(True)
        self.btn_gen_script.setText("✨ Tạo Kịch Bản (Gemini)")
        QMessageBox.critical(self, "Lỗi AI", f"Có lỗi xảy ra: {err_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MagaRecapClone()
    window.show()
    sys.exit(app.exec())