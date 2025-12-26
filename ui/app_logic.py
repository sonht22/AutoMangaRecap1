import os
import shutil
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem, QListWidgetItem, QProgressDialog, QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None
import json
try:
    import easyocr # Thư viện đọc chữ AI
except ImportError:
    easyocr = None

# --- IMPORT MODULE AN TOÀN ---
smart_cut = None
try:
    import cv2 
    from core import smart_cut
except ImportError as e:
    print(f"Lỗi Import: {e}")


class AppLogic:
    def __init__(self, main_window):
        self.ui = main_window 
        
        self.current_folder = ""
        self.current_file_path = ""
        self.current_cv_image = None
        
        self.cached_rects = {} 
        self.is_renaming = False
        
        self.setup_connections()
        
    def setup_connections(self):
        dock = self.ui.panel_dock
        dock.btn_scan.clicked.connect(self.action_auto_scan)
        dock.btn_add.clicked.connect(self.ui.viewer.add_manual_rect)
        dock.btn_del.clicked.connect(self.ui.viewer.delete_selected)
        dock.btn_clear_all.clicked.connect(self.action_reset_all)
        try: dock.btn_cut_trigger.clicked.disconnect()
        except: pass
        dock.btn_cut_trigger.clicked.connect(self.action_smart_cut)
        self.ui.image_list.itemChanged.connect(self.handle_rename_file)
        if hasattr(self.ui.image_list, 'orderChanged'):
            self.ui.image_list.orderChanged.connect(self.sync_table_order)
        if hasattr(self.ui, 'toolbar'):
            if hasattr(self.ui.toolbar, 'action_open'):
                try: self.ui.toolbar.action_open.triggered.disconnect()
                except: pass
                self.ui.toolbar.action_open.triggered.connect(self.action_load_folder)
            if hasattr(self.ui.toolbar, 'action_sort'):
                try: self.ui.toolbar.action_sort.triggered.disconnect()
                except: pass
                self.ui.toolbar.action_sort.triggered.connect(self.action_auto_sort)
        if hasattr(self.ui, 'trans_dock'):
            dock_trans = self.ui.trans_dock
            dock_trans.btn_ocr.clicked.connect(self.action_ocr_scan)
            dock_trans.btn_translate.clicked.connect(self.action_translate_text)
    # --- CÁC HÀM XỬ LÝ DỊCH THUẬT (PLACEHOLDER) ---
    def action_ocr_scan(self):
        """
        Thực hiện quét OCR sử dụng thư viện EasyOCR.
        - Đọc file nhị phân để tránh lỗi đường dẫn có dấu.
        - Căn chỉnh text lên trên cùng (Top-Left) cho gọn.
        """
        # 1. Kiểm tra thư viện
        if easyocr is None:
            QMessageBox.critical(self.ui, "Thiếu thư viện", "Chưa cài 'easyocr'.\nHãy chạy lệnh: pip install easyocr")
            return

        # 2. Kiểm tra dữ liệu bảng
        row_count = self.ui.table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self.ui, "Trống", "Chưa có ảnh nào trong danh sách để quét!")
            return

        # 3. Lấy ngôn ngữ từ Panel Dịch
        lang_text = "Tiếng Anh" # Mặc định
        if hasattr(self.ui, 'trans_dock'):
            lang_text = self.ui.trans_dock.combo_src_lang.currentText()

        langs = ['en'] 
        if "Tiếng Nhật" in lang_text: langs = ['ja', 'en']
        elif "Tiếng Hàn" in lang_text: langs = ['ko', 'en']
        elif "Tiếng Trung" in lang_text: langs = ['ch_sim', 'en']
        elif "Tiếng Việt" in lang_text: langs = ['vi', 'en']

        # 4. Xác định các dòng cần quét
        selected_rows = sorted(list(set([item.row() for item in self.ui.table.selectedItems()])))
        
        rows_to_process = []
        if selected_rows:
            rows_to_process = selected_rows
        else:
            # Nếu không chọn dòng nào, hỏi quét toàn bộ
            reply = QMessageBox.question(self.ui, "OCR", f"Bạn có muốn quét toàn bộ {row_count} ảnh không?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                rows_to_process = range(row_count)
            else:
                return

        # 5. Khởi tạo AI (Reader)
        progress = QProgressDialog("Đang tải AI Model (EasyOCR)...", "Hủy", 0, len(rows_to_process), self.ui)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            reader = easyocr.Reader(langs, gpu=False) # Đổi gpu=True nếu máy có card rời
        except Exception as e:
            progress.close()
            QMessageBox.critical(self.ui, "Lỗi AI", f"Không thể khởi tạo OCR:\n{e}")
            return

        # 6. Bắt đầu vòng lặp quét
        progress.setLabelText("Đang đọc văn bản từ ảnh...")
        
        for i, row in enumerate(rows_to_process):
            if progress.wasCanceled(): break
            
            # Lấy tên file
            item_name = self.ui.table.item(row, 1)
            if not item_name: continue
            fname = item_name.text()
            
            # Tìm đường dẫn file (Ưu tiên folder cut_panels)
            path_cut = os.path.join(self.current_folder, "cut_panels", fname)
            path_root = os.path.join(self.current_folder, fname)
            
            final_path = ""
            if os.path.exists(path_cut): final_path = path_cut
            elif os.path.exists(path_root): final_path = path_root
            else:
                self.ui.table.setItem(row, 2, QTableWidgetItem("Lỗi: Không tìm thấy file"))
                continue

            try:
                # --- ĐỌC FILE BINARY (Fix lỗi đường dẫn tiếng Việt) ---
                with open(final_path, "rb") as f:
                    file_bytes = f.read()
                
                # Chạy OCR
                results = reader.readtext(file_bytes, detail=0, paragraph=True)
                
                # Xử lý kết quả: Nối dòng và xóa khoảng trắng thừa đầu đuôi
                full_text = "\n".join(results).strip()
                
                # --- TẠO ITEM VÀ CĂN CHỈNH ---
                item_text = QTableWidgetItem(full_text)
                # Căn Trái + Lên Trên Cùng (Để bảng nhìn gọn, không bị lơ lửng giữa ô)
                item_text.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                
                self.ui.table.setItem(row, 2, item_text)
                
                # Cuộn bảng xuống dòng đang chạy
                self.ui.table.scrollToItem(self.ui.table.item(row, 0))
                
            except Exception as e:
                print(f"Lỗi OCR {fname}: {e}")
                self.ui.table.setItem(row, 2, QTableWidgetItem("Lỗi Scan"))

            progress.setValue(i + 1)
            QApplication.processEvents()

        QMessageBox.information(self.ui, "Hoàn tất", "Đã quét xong văn bản!")

    def action_translate_text(self):
        """
        Dịch văn bản sử dụng thư viện deep-translator (Google Translate).
        Ổn định hơn và không gây xung đột thư viện.
        """
        # 1. Kiểm tra thư viện
        if GoogleTranslator is None:
            QMessageBox.critical(self.ui, "Thiếu thư viện", "Chưa cài 'deep-translator'.\nHãy chạy lệnh: pip install deep-translator")
            return

        # 2. Kiểm tra dữ liệu
        row_count = self.ui.table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self.ui, "Trống", "Không có dữ liệu để dịch!")
            return

        # 3. Lấy thông tin ngôn ngữ từ giao diện
        if not hasattr(self.ui, 'trans_dock'): return
        
        src_lang_ui = self.ui.trans_dock.combo_src_lang.currentText()
        tgt_lang_ui = self.ui.trans_dock.combo_target_lang.currentText()
        
        # Mapping ngôn ngữ sang mã chuẩn (ISO 639-1)
        def get_lang_code(ui_text):
            if "Tiếng Việt" in ui_text: return 'vi'
            if "Tiếng Anh" in ui_text: return 'en'
            if "Tiếng Hàn" in ui_text: return 'ko'
            if "Tiếng Nhật" in ui_text: return 'ja'
            if "Tiếng Trung" in ui_text: return 'zh-CN'
            return 'auto' # Tự động phát hiện

        src_code = get_lang_code(src_lang_ui)
        tgt_code = get_lang_code(tgt_lang_ui)

        # 4. Xác định dòng cần dịch
        selected_rows = sorted(list(set([item.row() for item in self.ui.table.selectedItems()])))
        rows_to_process = selected_rows if selected_rows else range(row_count)

        # 5. Bắt đầu dịch
        progress = QProgressDialog("Đang dịch (deep-translator)...", "Hủy", 0, len(rows_to_process), self.ui)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        # Khởi tạo công cụ dịch (Nếu nguồn trùng đích thì thôi)
        translator = None
        if src_code != tgt_code:
            try:
                translator = GoogleTranslator(source=src_code, target=tgt_code)
            except Exception as e:
                QMessageBox.critical(self.ui, "Lỗi", f"Không thể khởi tạo dịch:\n{e}")
                return

        for i, row in enumerate(rows_to_process):
            if progress.wasCanceled(): break
            
            # Lấy text gốc từ cột OCR (Cột 2)
            item_ocr = self.ui.table.item(row, 2)
            ocr_text = item_ocr.text() if item_ocr else ""
            
            if not ocr_text.strip(): 
                progress.setValue(i + 1)
                continue
                
            final_text = ""
            
            # --- LOGIC DỊCH ---
            if src_code == tgt_code or translator is None:
                # COPY Y NGUYÊN
                final_text = ocr_text
            else:
                # DỊCH THẬT
                try:
                    # deep-translator hỗ trợ text dài tốt hơn
                    final_text = translator.translate(ocr_text)
                except Exception as e:
                    print(f"Lỗi dịch dòng {row}: {e}")
                    final_text = "Lỗi mạng/API"

            # --- ĐIỀN VÀO BẢNG (CỘT 3) ---
            item_trans = QTableWidgetItem(final_text)
            item_trans.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            self.ui.table.setItem(row, 3, item_trans)
            self.ui.table.resizeRowToContents(row)
            self.ui.table.scrollToItem(self.ui.table.item(row, 0))
            
            progress.setValue(i + 1)
            QApplication.processEvents()

        QMessageBox.information(self.ui, "Hoàn tất", "Đã xử lý xong văn bản!")
               

    def action_reset_all(self):
        if not self.current_folder: return
        reply = QMessageBox.question(self.ui, "Làm mới tất cả", 
                                     "Bạn có chắc muốn xóa hết dữ liệu khung đã quét và tải lại danh sách không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.cached_rects = {}
            self.current_cv_image = None
            self.ui.viewer.clear_rects()
            self.reload_list()
            QMessageBox.information(self.ui, "Đã làm mới", "Đã reset dữ liệu và cập nhật lại danh sách file!")

    def action_load_folder(self):
        folder = QFileDialog.getExistingDirectory(self.ui, "Chọn Folder Truyện")
        if folder:
            self.current_folder = folder
            self.cached_rects = {} 
            self.reload_list()

    def reload_list(self):
        # 1. Xóa sạch dữ liệu cũ ở cả List và Table
        self.ui.image_list.clear()
        self.ui.table.setRowCount(0) 
        
        if not self.current_folder: return
        
        if os.path.exists(self.current_folder):
            # Lấy danh sách file ảnh
            files = sorted([f for f in os.listdir(self.current_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))])
            
            self.is_renaming = True
            
            # 2. Duyệt qua từng file và thêm vào cả 2 nơi
            for i, f in enumerate(files):
                # --- Thêm vào List bên trái ---
                item = QListWidgetItem(f)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, f)
                self.ui.image_list.addItem(item)
                
                # --- [MỚI] Thêm vào Table bên phải ---
                self.ui.table.insertRow(i)
                # Cột 0: ID (1, 2, 3...)
                self.ui.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                # Cột 1: Tên File
                self.ui.table.setItem(i, 1, QTableWidgetItem(f))
                # Cột 2: OCR Text (Để trống)
                self.ui.table.setItem(i, 2, QTableWidgetItem(""))
                # Cột 3: Translation (Để trống)
                self.ui.table.setItem(i, 3, QTableWidgetItem(""))

            self.is_renaming = False
        else:
            QMessageBox.warning(self.ui, "Lỗi", "Thư mục không tồn tại!")

    def handle_rename_file(self, item):
        if self.is_renaming or not self.current_folder: return

        new_name = item.text()
        old_name = item.data(Qt.ItemDataRole.UserRole)
        
        if old_name and new_name != old_name:
            old_path = os.path.join(self.current_folder, old_name)
            new_path = os.path.join(self.current_folder, new_name)
            
            try:
                os.rename(old_path, new_path)
                
                # Cập nhật cache
                if old_name in self.cached_rects:
                    self.cached_rects[new_name] = self.cached_rects.pop(old_name)
                
                self.is_renaming = True
                item.setData(Qt.ItemDataRole.UserRole, new_name)
                self.is_renaming = False
                
                if self.current_file_path == old_path:
                    self.current_file_path = new_path
                
                # --- [MỚI] Cập nhật tên trong Bảng bên phải ---
                row = self.ui.image_list.row(item) # Tìm vị trí dòng
                if row >= 0:
                    self.ui.table.setItem(row, 1, QTableWidgetItem(new_name))
                    
            except Exception as e:
                self.is_renaming = True
                item.setText(old_name)
                self.is_renaming = False
                QMessageBox.warning(self.ui, "Lỗi", f"Không thể đổi tên file:\n{e}")

    def action_auto_sort(self):
        count = self.ui.image_list.count()
        if count == 0: return
        items = [self.ui.image_list.takeItem(0) for _ in range(count)]
        import re
        def natural_key(item):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', item.text())]
        items.sort(key=natural_key)
        for item in items: self.ui.image_list.addItem(item)

    def sync_table_order(self): pass

    def save_current_rects_to_cache(self):
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
            rects = self.ui.viewer.get_rects()
            self.cached_rects[filename] = rects

    def display_image(self, row):
        self.save_current_rects_to_cache()

        item = self.ui.image_list.item(row)
        if not item: return
        
        filename = item.text()
        path = os.path.join(self.current_folder, filename)
        if not os.path.exists(path): return

        self.current_file_path = path
        
        pixmap = QPixmap(path)
        # --- THAY ĐỔI Ở ĐÂY: maintain_zoom=True ---
        self.ui.viewer.set_image(pixmap, maintain_zoom=True) 
        # ------------------------------------------
        self.current_cv_image = None
        
        self.ui.viewer.clear_rects()
        if filename in self.cached_rects:
            for r in self.cached_rects[filename]:
                self.ui.viewer.add_rect(*r)
        
    def action_auto_scan(self):
        if smart_cut is None:
            QMessageBox.critical(self.ui, "Thiếu Thư Viện", "Chưa cài 'opencv-python' hoặc lỗi module core.")
            return
        if not self.current_folder: 
            QMessageBox.warning(self.ui, "Chưa chọn Folder", "Vui lòng chọn thư mục truyện trước!")
            return
        reply = QMessageBox.question(self.ui, "Quét Tự Động", 
                                     "Bạn muốn quét tất cả ảnh trong danh sách hay chỉ ảnh hiện tại?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        scan_all = (reply == QMessageBox.StandardButton.Yes)
        dock = self.ui.panel_dock
        w_adj = dock.spin_w.value()
        h_adj = dock.spin_h.value()
        if scan_all:
            count = self.ui.image_list.count()
            progress = QProgressDialog("Đang quét toàn bộ ảnh...", "Hủy", 0, count, self.ui)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            for i in range(count):
                if progress.wasCanceled(): break
                item = self.ui.image_list.item(i)
                fname = item.text()
                fpath = os.path.join(self.current_folder, fname)
                try:
                    rects, _ = smart_cut.analyze_panels_coordinates(fpath)
                    if rects is None: rects = []
                    adj_rects = [(x, y, w+w_adj, h+h_adj) for (x,y,w,h) in rects]
                    self.cached_rects[fname] = adj_rects
                except Exception as e:
                    print(f"Lỗi quét {fname}: {e}")
                progress.setValue(i + 1)
            current_name = os.path.basename(self.current_file_path) if self.current_file_path else ""
            if current_name in self.cached_rects:
                self.ui.viewer.clear_rects()
                for r in self.cached_rects[current_name]:
                    self.ui.viewer.add_rect(*r)
            QMessageBox.information(self.ui, "Xong", "Đã quét xong toàn bộ danh sách!")
        else:
            if not self.current_file_path: return
            try:
                rects, cv_img = smart_cut.analyze_panels_coordinates(self.current_file_path)
                if rects is None: rects = []
                self.current_cv_image = cv_img 
                self.ui.viewer.clear_rects()
                for (x, y, w, h) in rects:
                    self.ui.viewer.add_rect(x, y, w + w_adj, h + h_adj)
                self.save_current_rects_to_cache()
            except Exception as e:
                QMessageBox.critical(self.ui, "Lỗi", f"Lỗi quét ảnh này: {e}")

    def action_smart_cut(self):
        if smart_cut is None: return
        self.save_current_rects_to_cache()
        if not self.cached_rects:
            QMessageBox.warning(self.ui, "Chưa có dữ liệu", "Vui lòng Scan ảnh hoặc thêm khung trước!")
            return
        count_cached = len(self.cached_rects)
        reply = QMessageBox.question(self.ui, "Cắt Panel", 
                                     f"Bạn đang có dữ liệu khung của {count_cached} ảnh.\nBạn muốn cắt TOÀN BỘ hay chỉ ẢNH HIỆN TẠI?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        cut_all = (reply == QMessageBox.StandardButton.Yes)
        dock = self.ui.panel_dock
        output_folder = os.path.join(self.current_folder, "cut_panels")
        files_to_process = []
        if cut_all:
            for fname, rects in self.cached_rects.items():
                if rects: files_to_process.append((fname, rects))
        else:
            curr_name = os.path.basename(self.current_file_path) if self.current_file_path else ""
            if curr_name in self.cached_rects:
                files_to_process.append((curr_name, self.cached_rects[curr_name]))
        if not files_to_process: return
        progress = QProgressDialog("Đang cắt và lưu ảnh...", "Hủy", 0, len(files_to_process), self.ui)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        saved_paths_all = []
        for i, (fname, rects) in enumerate(files_to_process):
            if progress.wasCanceled(): break
            fpath = os.path.join(self.current_folder, fname)
            if dock.radio_top.isChecked(): rects.sort(key=lambda r: r[1])
            else: rects.sort(key=lambda r: r[0])
            try:
                stream = open(fpath, "rb")
                bytes_data = bytearray(stream.read())
                import numpy as np
                np_arr = np.asarray(bytes_data, dtype=np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    prefix = os.path.splitext(fname)[0] + "_p"
                    saved = smart_cut.save_cropped_images(img, rects, output_folder, file_prefix=prefix)
                    saved_paths_all.extend(saved)
            except Exception as e:
                print(f"Lỗi cắt {fname}: {e}")
            progress.setValue(i + 1)
        QMessageBox.information(self.ui, "Hoàn tất", f"Đã lưu {len(saved_paths_all)} panel vào:\n{output_folder}")
        self.update_table_results(saved_paths_all)

    def update_table_results(self, files):
        self.ui.table.setRowCount(0)
        for i, path in enumerate(files):
            filename = os.path.basename(path)
            self.ui.table.insertRow(i)
            self.ui.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.ui.table.setItem(i, 1, QTableWidgetItem(filename))

    # --- [MỚI] HÀM LƯU DỰ ÁN ---
    def save_project(self):
        if not self.current_folder:
            QMessageBox.warning(self.ui, "Lỗi", "Chưa có dự án nào đang mở để lưu!")
            return

        # 1. Thu thập dữ liệu từ Bảng (Table)
        table_data = []
        for row in range(self.ui.table.rowCount()):
            # Lấy thông tin từng cột: ID, Tên file, OCR, Dịch
            item_id = self.ui.table.item(row, 0).text() if self.ui.table.item(row, 0) else ""
            item_file = self.ui.table.item(row, 1).text() if self.ui.table.item(row, 1) else ""
            item_ocr = self.ui.table.item(row, 2).text() if self.ui.table.item(row, 2) else ""
            
            # (Nếu sau này bạn hiện cột dịch thì lấy thêm, tạm thời để trống)
            item_trans = "" 

            table_data.append({
                "id": item_id,
                "file": item_file,
                "ocr": item_ocr,
                "trans": item_trans
            })

        # 2. Đóng gói toàn bộ dữ liệu
        project_data = {
            "folder_path": self.current_folder,      # Đường dẫn thư mục gốc
            "cached_rects": self.cached_rects,       # Các khung đã vẽ tay
            "table_data": table_data                 # Nội dung text đã làm
        }

        # 3. Chọn nơi lưu
        file_path, _ = QFileDialog.getSaveFileName(self.ui, "Lưu File Dự Án", self.current_folder, "JSON Files (*.json)")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self.ui, "Thành công", "Đã lưu dự án thành công!")
            except Exception as e:
                QMessageBox.critical(self.ui, "Lỗi", f"Không thể lưu file:\n{e}")

    # --- [MỚI] HÀM MỞ DỰ ÁN ---
    def load_project(self):
        # 1. Chọn file json
        file_path, _ = QFileDialog.getOpenFileName(self.ui, "Mở File Dự Án", "", "JSON Files (*.json)")
        
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # 2. Khôi phục Folder gốc
            folder_path = project_data.get("folder_path", "")
            if os.path.exists(folder_path):
                self.current_folder = folder_path
                self.reload_list() # Load lại danh sách file bên trái
            else:
                QMessageBox.warning(self.ui, "Cảnh báo", f"Thư mục gốc không còn tồn tại:\n{folder_path}\nBạn cần chọn lại folder thủ công.")
            
            # 3. Khôi phục các khung đã vẽ (cached_rects)
            self.cached_rects = project_data.get("cached_rects", {})
            
            # 4. Khôi phục Bảng dữ liệu (Quan trọng nhất)
            saved_table = project_data.get("table_data", [])
            
            self.ui.table.setRowCount(0) # Xóa bảng cũ
            
            for i, row_data in enumerate(saved_table):
                self.ui.table.insertRow(i)
                
                # Điền ID
                self.ui.table.setItem(i, 0, QTableWidgetItem(row_data.get("id", str(i+1))))
                
                # Điền Tên File
                self.ui.table.setItem(i, 1, QTableWidgetItem(row_data.get("file", "")))
                
                # Điền OCR Text
                item_ocr = QTableWidgetItem(row_data.get("ocr", ""))
                # Căn chỉnh lại cho đẹp (như code trước)
                item_ocr.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                self.ui.table.setItem(i, 2, item_ocr)
                
                # Điền Dịch (nếu có)
                self.ui.table.setItem(i, 3, QTableWidgetItem(row_data.get("trans", "")))
            
            # Resize dòng cho vừa chữ
            self.ui.table.resizeRowsToContents()
            
            QMessageBox.information(self.ui, "Thành công", "Đã tải lại dự án cũ!")

        except Exception as e:
            QMessageBox.critical(self.ui, "Lỗi", f"File dự án bị lỗi hoặc không đúng định dạng:\n{e}")        