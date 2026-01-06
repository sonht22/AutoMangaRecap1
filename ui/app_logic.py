import os
import shutil
import time 
import requests 
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem, QListWidgetItem, QProgressDialog, QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import json

# --- IMPORT CÁC THƯ VIỆN CẦN THIẾT ---
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

try:
    import easyocr 
except ImportError:
    easyocr = None

smart_cut = None
try:
    import cv2 
    from core import smart_cut
except ImportError as e:
    print(f"Lỗi Import Core: {e}")

# Import hàm xử lý ảnh OCR (Nếu có)
try:
    from core.ocr_utils import preprocess_image
except ImportError:
    preprocess_image = None


class AppLogic:
    def __init__(self, main_window):
        self.ui = main_window 
        self.current_folder = ""
        self.current_file_path = ""
        self.current_cv_image = None
        
        # Biến nhớ file dự án (.json)
        self.current_project_file = None 
        
        self.cached_rects = {} 
        self.is_renaming = False

        # [MỚI] Cờ để kiểm soát đồng bộ (tránh vòng lặp vô tận)
        self.is_syncing = False 
        
        # Khởi tạo kết nối ngay khi chạy
        self.setup_connections()
        
    def setup_connections(self):
        """KẾT NỐI TÍN HIỆU TỪ GIAO DIỆN XUỐNG LOGIC"""
        
        # 1. KẾT NỐI DANH SÁCH ẢNH & TABLE (ĐỒNG BỘ 2 CHIỀU)
        # Khi bấm vào item trong List -> Gọi hàm sync_from_list
        self.ui.image_list.itemClicked.connect(self.sync_from_list)
        # Khi đổi tên file
        self.ui.image_list.itemChanged.connect(self.handle_rename_file)
        
        # Khi bấm vào ô trong Table -> Gọi hàm sync_from_table
        self.ui.table.cellClicked.connect(self.sync_from_table)
        # Khi dùng phím mũi tên lên xuống trong Table
        self.ui.table.currentCellChanged.connect(self.sync_from_table_keyboard)

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

        # 2. KẾT NỐI PANEL CẮT (PANEL DOCK)
        if hasattr(self.ui, 'panel_dock'):
            dock = self.ui.panel_dock
            dock.btn_scan.clicked.connect(self.action_auto_scan)
            dock.btn_add.clicked.connect(self.ui.viewer.add_manual_rect)
            dock.btn_del.clicked.connect(self.ui.viewer.delete_selected)
            dock.btn_clear_all.clicked.connect(self.action_reset_all)
            try: dock.btn_cut_trigger.clicked.disconnect()
            except: pass
            dock.btn_cut_trigger.clicked.connect(self.action_smart_cut)

        # 3. KẾT NỐI PANEL DỊCH & TTS (TRANS DOCK)
        if hasattr(self.ui, 'trans_dock'):
            dock_trans = self.ui.trans_dock
            dock_trans.btn_ocr.clicked.connect(self.action_ocr_scan)
            dock_trans.btn_translate.clicked.connect(self.action_translate_text)
            dock_trans.btn_tts.clicked.connect(self.action_generate_audio)
            
            if hasattr(dock_trans, 'combo_provider'):
                dock_trans.combo_provider.currentIndexChanged.connect(self.update_tts_options)

    # --- [MỚI] CÁC HÀM ĐỒNG BỘ HÓA (CORE LOGIC) ---
    
    def sync_from_list(self, item):
        """Khi click vào List bên trái -> Đồng bộ sang Table và hiển thị ảnh"""
        if self.is_syncing: return # Nếu đang đồng bộ thì thôi, tránh lặp
        
        self.is_syncing = True
        try:
            row = self.ui.image_list.row(item)
            # 1. Hiển thị ảnh
            self.display_image(row)
            # 2. Chọn dòng tương ứng bên Table
            self.ui.table.selectRow(row)
        finally:
            self.is_syncing = False

    def sync_from_table(self, row, col):
        """Khi click vào Table bên phải -> Đồng bộ sang List và hiển thị ảnh"""
        if self.is_syncing: return
        
        self.is_syncing = True
        try:
            # 1. Chọn item tương ứng bên List
            self.ui.image_list.setCurrentRow(row)
            # 2. Hiển thị ảnh
            self.display_image(row)
        finally:
            self.is_syncing = False

    def sync_from_table_keyboard(self, currentRow, currentColumn, previousRow, previousColumn):
        """Hỗ trợ khi dùng phím mũi tên trong bảng"""
        if currentRow != previousRow and currentRow >= 0:
            self.sync_from_table(currentRow, 0)

    # --- HÀM HIỂN THỊ ẢNH (QUAN TRỌNG) ---
    def display_image(self, row):
        # 1. Lưu lại khung cắt của ảnh cũ (nếu có) trước khi chuyển
        self.save_current_rects_to_cache()
        
        # 2. Lấy tên file từ List
        item = self.ui.image_list.item(row)
        if not item: return
        
        filename = item.text()
        path = os.path.join(self.current_folder, filename)
        
        if not os.path.exists(path): return
        
        self.current_file_path = path
        
        # 3. Hiển thị ảnh lên Viewer
        # Dùng hàm đọc ảnh UTF-8 (nếu có) hoặc mặc định
        try:
            from core.ocr_utils import read_image_utf8
            cv_img = read_image_utf8(path)
            if cv_img is not None:
                # Convert CV2 to QPixmap để hiển thị
                height, width, channel = cv_img.shape
                bytesPerLine = 3 * width
                # Chuyển BGR sang RGB
                cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                from PyQt6.QtGui import QImage
                qImg = QImage(cv_img_rgb.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
                self.ui.viewer.set_image(QPixmap.fromImage(qImg), maintain_zoom=True)
            else:
                self.ui.viewer.set_image(QPixmap(path), maintain_zoom=True)
        except:
             self.ui.viewer.set_image(QPixmap(path), maintain_zoom=True)
        
        self.current_cv_image = None
        
        # 4. Load lại các khung cắt đã lưu (nếu có)
        self.ui.viewer.clear_rects()
        if filename in self.cached_rects:
            for r in self.cached_rects[filename]: 
                self.ui.viewer.add_rect(*r)

    # --- HÀM CẬP NHẬT MODEL TTS ---
    def update_tts_options(self):
        dock = self.ui.trans_dock
        provider = dock.combo_provider.currentText()
        dock.combo_model.clear()
        
        if provider == "Minimax":
            dock.combo_model.addItems(["speech-01-turbo", "speech-01-hd", "speech-2.6-hd"])
            dock.combo_voice.setPlaceholderText("Nhập ID Minimax (VD: 2095...)")
        else:
            dock.combo_model.addItems(["eleven_multilingual_v2", "eleven_turbo_v2"])
            dock.combo_voice.setPlaceholderText("Nhập ID ElevenLabs...")

    # --- 1. HÀM OCR (ĐÃ CÓ XỬ LÝ ẢNH) ---
    def action_ocr_scan(self):
        if easyocr is None:
            QMessageBox.critical(self.ui, "Thiếu thư viện", "Chưa cài 'easyocr'.")
            return

        row_count = self.ui.table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self.ui, "Trống", "Chưa có ảnh nào!")
            return

        lang_text = "Tiếng Anh"
        if hasattr(self.ui, 'trans_dock'):
            lang_text = self.ui.trans_dock.combo_src_lang.currentText()

        langs = ['en'] 
        if "Tiếng Nhật" in lang_text: langs = ['ja', 'en']
        elif "Tiếng Hàn" in lang_text: langs = ['ko', 'en']
        elif "Tiếng Trung" in lang_text: langs = ['ch_sim', 'en']
        elif "Tiếng Việt" in lang_text: langs = ['vi', 'en']

        selected_rows = sorted(list(set([item.row() for item in self.ui.table.selectedItems()])))
        rows_to_process = selected_rows if selected_rows else range(row_count)
        
        if not selected_rows:
            reply = QMessageBox.question(self.ui, "OCR", f"Quét toàn bộ {row_count} ảnh?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes: return
            rows_to_process = range(row_count)

        progress = QProgressDialog("Đang tải AI Model (EasyOCR)...", "Hủy", 0, len(rows_to_process), self.ui)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            reader = easyocr.Reader(langs, gpu=False)
        except Exception as e:
            progress.close()
            QMessageBox.critical(self.ui, "Lỗi AI", f"Không thể khởi tạo OCR:\n{e}")
            return

        progress.setLabelText("Đang đọc văn bản...")
        for i, row in enumerate(rows_to_process):
            if progress.wasCanceled(): break
            
            item_name = self.ui.table.item(row, 1)
            if not item_name: continue
            fname = item_name.text()
            
            path_cut = os.path.join(self.current_folder, "cut_panels", fname)
            path_root = os.path.join(self.current_folder, fname)
            
            final_path = ""
            if os.path.exists(path_cut): final_path = path_cut
            elif os.path.exists(path_root): final_path = path_root
            else:
                self.ui.table.setItem(row, 2, QTableWidgetItem("Lỗi file"))
                continue

            try:
                # --- XỬ LÝ ẢNH TRƯỚC KHI QUÉT ---
                image_input = None
                if preprocess_image:
                    try:
                        image_input = preprocess_image(final_path)
                    except Exception as err:
                        print(f"Lỗi xử lý ảnh {fname}: {err}")
                        image_input = None 
                
                if image_input is None:
                    # Nếu không xử lý được (hoặc không import được), đọc thủ công fix lỗi tiếng Việt
                    try:
                        from core.ocr_utils import read_image_utf8
                        image_input = read_image_utf8(final_path)
                    except:
                        with open(final_path, "rb") as f: image_input = f.read()

                results = reader.readtext(image_input, detail=0, paragraph=True, batch_size=4)
                full_text = "\n".join(results).strip()
                
                item_text = QTableWidgetItem(full_text)
                item_text.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                self.ui.table.setItem(row, 2, item_text)
                self.ui.table.resizeRowToContents(row)
                self.ui.table.scrollToItem(self.ui.table.item(row, 0))
            except Exception as e:
                print(f"Lỗi OCR {fname}: {e}")
                self.ui.table.setItem(row, 2, QTableWidgetItem("Lỗi Scan"))

            progress.setValue(i + 1)
            QApplication.processEvents()
        
        QMessageBox.information(self.ui, "Hoàn tất", "Đã quét xong văn bản!")

    # --- 2. HÀM DỊCH THUẬT (GIỮ NGUYÊN) ---
    def action_translate_text(self):
        if GoogleTranslator is None:
            QMessageBox.critical(self.ui, "Thiếu thư viện", "Chưa cài 'deep-translator'.")
            return

        row_count = self.ui.table.rowCount()
        if row_count == 0: return

        if not hasattr(self.ui, 'trans_dock'): return
        
        src_lang_ui = self.ui.trans_dock.combo_src_lang.currentText()
        tgt_lang_ui = self.ui.trans_dock.combo_target_lang.currentText()
        
        def get_lang_code(ui_text):
            if "Tiếng Việt" in ui_text: return 'vi'
            if "Tiếng Anh" in ui_text: return 'en'
            if "Tiếng Hàn" in ui_text: return 'ko'
            if "Tiếng Nhật" in ui_text: return 'ja'
            if "Tiếng Trung" in ui_text: return 'zh-CN'
            return 'auto'

        src_code = get_lang_code(src_lang_ui)
        tgt_code = get_lang_code(tgt_lang_ui)

        selected_rows = sorted(list(set([item.row() for item in self.ui.table.selectedItems()])))
        rows_to_process = []
        
        if len(selected_rows) > 0:
            msg = QMessageBox(self.ui)
            msg.setWindowTitle("Tùy chọn dịch")
            msg.setText(f"Bạn đang chọn {len(selected_rows)} dòng.")
            msg.setInformativeText("Bạn muốn dịch dòng đã chọn hay dịch TẤT CẢ?")
            btn_sel = msg.addButton("Chỉ dòng đã chọn", QMessageBox.ButtonRole.ActionRole)
            btn_all = msg.addButton("Dịch TẤT CẢ", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            
            if msg.clickedButton() == btn_sel: rows_to_process = selected_rows
            elif msg.clickedButton() == btn_all: rows_to_process = range(row_count)
            else: return
        else:
            reply = QMessageBox.question(self.ui, "Xác nhận", f"Dịch toàn bộ {row_count} dòng?", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes: rows_to_process = range(row_count)
            else: return

        progress = QProgressDialog("Đang dịch...", "Hủy", 0, len(rows_to_process), self.ui)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        translator = None
        if src_code != tgt_code:
            try: translator = GoogleTranslator(source=src_code, target=tgt_code)
            except Exception as e:
                progress.close()
                QMessageBox.critical(self.ui, "Lỗi", f"Lỗi khởi tạo dịch:\n{e}")
                return

        for i, row in enumerate(rows_to_process):
            if progress.wasCanceled(): break
            
            item_ocr = self.ui.table.item(row, 2)
            ocr_text = item_ocr.text() if item_ocr else ""
            
            if not ocr_text.strip(): 
                progress.setValue(i + 1)
                continue
                
            final_text = ""
            if src_code == tgt_code or translator is None:
                final_text = ocr_text
            else:
                try: final_text = translator.translate(ocr_text)
                except: final_text = "Lỗi mạng"

            item_trans = QTableWidgetItem(final_text)
            item_trans.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.ui.table.setItem(row, 3, item_trans)
            self.ui.table.resizeRowToContents(row)
            self.ui.table.scrollToItem(self.ui.table.item(row, 0))
            
            progress.setValue(i + 1)
            QApplication.processEvents()

        QMessageBox.information(self.ui, "Hoàn tất", "Đã dịch xong!")

    # --- 3. HÀM TẠO AUDIO ---
    def action_generate_audio(self):
        try: import requests
        except ImportError: return

        dock = self.ui.trans_dock
        api_key = dock.txt_api_key.text().strip()
        
        if not api_key:
            QMessageBox.warning(self.ui, "Thiếu API Key", "Vui lòng nhập API Key.")
            return

        provider = dock.combo_provider.currentText()
        model_id = dock.combo_model.currentText()
        
        voice_id = dock.combo_voice.currentData()
        if not voice_id:
            raw_text = dock.combo_voice.currentText().strip()
            if "(" in raw_text and ")" in raw_text:
                voice_id = raw_text.split("(")[-1].replace(")", "").strip()
            else:
                voice_id = raw_text

        if not voice_id:
            QMessageBox.warning(self.ui, "Thiếu Voice ID", "Vui lòng nhập Voice ID.")
            return

        row_count = self.ui.table.rowCount()
        selected_rows = sorted(list(set([item.row() for item in self.ui.table.selectedItems()])))
        rows_to_process = selected_rows if selected_rows else range(row_count)

        audio_dir = os.path.join(self.current_folder, "audio_files")
        if not os.path.exists(audio_dir): os.makedirs(audio_dir)

        progress = QProgressDialog(f"Đang kết nối {provider}...", "Hủy", 0, len(rows_to_process), self.ui)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        headers = {
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }

        for i, row in enumerate(rows_to_process):
            if progress.wasCanceled(): break

            text_to_speak = ""
            if self.ui.table.item(row, 3): text_to_speak = self.ui.table.item(row, 3).text()
            if not text_to_speak.strip() and self.ui.table.item(row, 2):
                text_to_speak = self.ui.table.item(row, 2).text()
            
            if not text_to_speak.strip():
                progress.setValue(i+1)
                continue

            try:
                if provider == "Minimax":
                    url_create = "https://api.ai33.pro/v1m/task/text-to-speech"
                    payload = {
                        "text": text_to_speak,
                        "model": "speech-01-turbo",
                        "voice_setting": {
                            "voice_id": voice_id,
                            "vol": 1, "pitch": 0, "speed": 1
                        },
                        "language_boost": "Auto"
                    }
                    if "hd" in model_id.lower(): payload["model"] = model_id
                    
                else: 
                    url_create = f"https://api.ai33.pro/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"
                    payload = {
                        "text": text_to_speak,
                        "model_id": "eleven_multilingual_v2",
                        "with_transcript": False
                    }

                progress.setLabelText(f"Dòng {row+1}: Gửi yêu cầu...")
                QApplication.processEvents()
                
                response = requests.post(url_create, json=payload, headers=headers)
                
                if response.status_code != 200:
                    err = f"Lỗi {response.status_code}"
                    print(f"API Error: {response.text}")
                    self.ui.table.setItem(row, 4, QTableWidgetItem(err))
                    continue

                resp_json = response.json()
                if not resp_json.get("success"):
                     msg = resp_json.get("message", "Từ chối")
                     self.ui.table.setItem(row, 4, QTableWidgetItem(f"Lỗi: {msg}"))
                     continue
                
                task_id = resp_json.get("task_id")
                
                progress.setLabelText(f"Dòng {row+1}: Đang xử lý...")
                audio_url = None
                for _ in range(30):
                    time.sleep(1.5)
                    check_resp = requests.get(f"https://api.ai33.pro/v1/task/{task_id}", headers=headers)
                    if check_resp.status_code == 200:
                        task_data = check_resp.json()
                        if task_data.get("status") == "done":
                            audio_url = task_data.get("metadata", {}).get("audio_url")
                            break
                        elif task_data.get("status") == "failed": break
                    QApplication.processEvents()

                if audio_url:
                    file_name = f"voi_{row}_{provider}_{int(time.time())}.mp3"
                    with open(os.path.join(audio_dir, file_name), 'wb') as f:
                        f.write(requests.get(audio_url).content)
                    self.ui.table.setItem(row, 4, QTableWidgetItem(file_name))
                else:
                    self.ui.table.setItem(row, 4, QTableWidgetItem("Thất bại"))

            except Exception as e:
                print(e)
                self.ui.table.setItem(row, 4, QTableWidgetItem("Lỗi Code"))
            
            progress.setValue(i+1)
        
        QMessageBox.information(self.ui, "Hoàn tất", "Xử lý xong!")

    # --- CÁC HÀM CƠ BẢN KHÁC ---
    def action_reset_all(self):
        if not self.current_folder: return
        reply = QMessageBox.question(self.ui, "Làm mới tất cả", "Reset dữ liệu?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.cached_rects = {}
            self.ui.viewer.clear_rects()
            self.reload_list()

    def action_load_folder(self):
        folder = QFileDialog.getExistingDirectory(self.ui, "Chọn Folder Truyện")
        if folder:
            self.current_folder = folder
            self.cached_rects = {} 
            self.reload_list()

    def reload_list(self):
        self.ui.image_list.clear()
        self.ui.table.setRowCount(0) 
        if not self.current_folder: return
        if os.path.exists(self.current_folder):
            files = sorted([f for f in os.listdir(self.current_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))])
            self.is_renaming = True
            for i, f in enumerate(files):
                item = QListWidgetItem(f)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, f)
                self.ui.image_list.addItem(item)
                
                self.ui.table.insertRow(i)
                self.ui.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.ui.table.setItem(i, 1, QTableWidgetItem(f))
                self.ui.table.setItem(i, 2, QTableWidgetItem(""))
                self.ui.table.setItem(i, 3, QTableWidgetItem(""))
                self.ui.table.setItem(i, 4, QTableWidgetItem("")) # VOI
            self.is_renaming = False
            self.ui.table.resizeRowsToContents()

    def handle_rename_file(self, item):
        if self.is_renaming or not self.current_folder: return
        new_name = item.text()
        old_name = item.data(Qt.ItemDataRole.UserRole)
        if old_name and new_name != old_name:
            old_path = os.path.join(self.current_folder, old_name)
            new_path = os.path.join(self.current_folder, new_name)
            try:
                os.rename(old_path, new_path)
                if old_name in self.cached_rects:
                    self.cached_rects[new_name] = self.cached_rects.pop(old_name)
                self.is_renaming = True
                item.setData(Qt.ItemDataRole.UserRole, new_name)
                self.is_renaming = False
                if self.current_file_path == old_path: self.current_file_path = new_path
                row = self.ui.image_list.row(item)
                if row >= 0: self.ui.table.setItem(row, 1, QTableWidgetItem(new_name))
            except Exception as e:
                self.is_renaming = True
                item.setText(old_name)
                self.is_renaming = False

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

    def action_auto_scan(self):
        if smart_cut is None:
            QMessageBox.critical(self.ui, "Lỗi", "Chưa cài 'opencv'.")
            return
        if not self.current_folder: return
        reply = QMessageBox.question(self.ui, "Quét Tự Động", "Quét toàn bộ ảnh?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        scan_all = (reply == QMessageBox.StandardButton.Yes)
        dock = self.ui.panel_dock
        w_adj = dock.spin_w.value()
        h_adj = dock.spin_h.value()
        if scan_all:
            count = self.ui.image_list.count()
            progress = QProgressDialog("Quét...", "Hủy", 0, count, self.ui)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            for i in range(count):
                if progress.wasCanceled(): break
                item = self.ui.image_list.item(i)
                fname = item.text()
                fpath = os.path.join(self.current_folder, fname)
                try:
                    # Dùng hàm đọc ảnh UTF-8
                    from core.ocr_utils import read_image_utf8
                    cv_img = read_image_utf8(fpath)
                    
                    rects = []
                    if cv_img is not None:
                         rects, _ = smart_cut.analyze_panels_coordinates(fpath) # Lưu ý: Smart cut của bạn cần hỗ trợ nhận numpy array, nếu không thì đoạn này vẫn có thể lỗi tên file
                    
                    if rects is None: rects = []
                    adj_rects = [(x, y, w+w_adj, h+h_adj) for (x,y,w,h) in rects]
                    self.cached_rects[fname] = adj_rects
                except: pass
                progress.setValue(i+1)
            QMessageBox.information(self.ui, "Xong", "Đã quét xong!")
        else:
            if not self.current_file_path: return
            rects, cv_img = smart_cut.analyze_panels_coordinates(self.current_file_path)
            if rects:
                self.current_cv_image = cv_img 
                self.ui.viewer.clear_rects()
                for (x, y, w, h) in rects: self.ui.viewer.add_rect(x, y, w+w_adj, h+h_adj)
                self.save_current_rects_to_cache()

    def action_smart_cut(self):
        if smart_cut is None: return
        self.save_current_rects_to_cache()
        if not self.cached_rects: return
        reply = QMessageBox.question(self.ui, "Cắt Panel", "Cắt toàn bộ hay chỉ ảnh này?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        cut_all = (reply == QMessageBox.StandardButton.Yes)
        dock = self.ui.panel_dock
        output_folder = os.path.join(self.current_folder, "cut_panels")
        if not os.path.exists(output_folder): os.makedirs(output_folder)
        
        files_to_process = []
        if cut_all:
            for f, r in self.cached_rects.items(): 
                if r: files_to_process.append((f, r))
        else:
            if self.current_file_path:
                curr = os.path.basename(self.current_file_path)
                if curr in self.cached_rects: files_to_process.append((curr, self.cached_rects[curr]))
        
        progress = QProgressDialog("Đang cắt...", "Hủy", 0, len(files_to_process), self.ui)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        saved_paths = []
        for i, (fname, rects) in enumerate(files_to_process):
            fpath = os.path.join(self.current_folder, fname)
            if dock.radio_top.isChecked(): rects.sort(key=lambda r: r[1])
            else: rects.sort(key=lambda r: r[0])
            try:
                # Dùng hàm đọc UTF-8
                from core.ocr_utils import read_image_utf8
                img = read_image_utf8(fpath)
                if img is not None:
                    prefix = os.path.splitext(fname)[0] + "_p"
                    saved = smart_cut.save_cropped_images(img, rects, output_folder, file_prefix=prefix)
                    saved_paths.extend(saved)
            except: pass
            progress.setValue(i+1)
            
        self.update_table_results(saved_paths)
        QMessageBox.information(self.ui, "Xong", f"Đã lưu tại: {output_folder}")

    def update_table_results(self, files):
        self.ui.table.setRowCount(0)
        for i, path in enumerate(files):
            self.ui.table.insertRow(i)
            self.ui.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.ui.table.setItem(i, 1, QTableWidgetItem(os.path.basename(path)))
            self.ui.table.setItem(i, 2, QTableWidgetItem(""))
            self.ui.table.setItem(i, 3, QTableWidgetItem(""))
            self.ui.table.setItem(i, 4, QTableWidgetItem(""))

    # --- LƯU / TẢI DỰ ÁN ---
    def _get_project_data(self):
        table_data = []
        for row in range(self.ui.table.rowCount()):
            item_id = self.ui.table.item(row, 0).text() if self.ui.table.item(row, 0) else ""
            item_file = self.ui.table.item(row, 1).text() if self.ui.table.item(row, 1) else ""
            item_ocr = self.ui.table.item(row, 2).text() if self.ui.table.item(row, 2) else ""
            item_trans = self.ui.table.item(row, 3).text() if self.ui.table.item(row, 3) else ""
            item_voi = self.ui.table.item(row, 4).text() if self.ui.table.item(row, 4) else ""
            table_data.append({"id": item_id, "file": item_file, "ocr": item_ocr, "trans": item_trans, "voi": item_voi})
        return {"folder_path": self.current_folder, "cached_rects": self.cached_rects, "table_data": table_data}

    def save_project(self):
        if not self.current_folder: return
        if not self.current_project_file: 
            self.save_project_as()
            return
        try:
            with open(self.current_project_file, 'w', encoding='utf-8') as f:
                json.dump(self._get_project_data(), f, ensure_ascii=False, indent=4)
            self.ui.statusBar().showMessage(f"Đã lưu: {os.path.basename(self.current_project_file)}", 3000)
        except Exception as e: QMessageBox.critical(self.ui, "Lỗi", str(e))

    def save_project_as(self):
        if not self.current_folder: return
        path, _ = QFileDialog.getSaveFileName(self.ui, "Lưu Dự Án", self.current_folder, "JSON Files (*.json)")
        if path:
            self.current_project_file = path
            self.save_project()
            self.ui.setWindowTitle(f"Project: {os.path.basename(path)}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self.ui, "Mở Dự Án", "", "JSON Files (*.json)")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
            folder = data.get("folder_path", "")
            if os.path.exists(folder):
                self.current_folder = folder
                self.reload_list()
            self.cached_rects = data.get("cached_rects", {})
            self.ui.table.setRowCount(0)
            for i, r in enumerate(data.get("table_data", [])):
                self.ui.table.insertRow(i)
                self.ui.table.setItem(i, 0, QTableWidgetItem(r.get("id", "")))
                self.ui.table.setItem(i, 1, QTableWidgetItem(r.get("file", "")))
                self.ui.table.setItem(i, 2, QTableWidgetItem(r.get("ocr", "")))
                self.ui.table.setItem(i, 3, QTableWidgetItem(r.get("trans", "")))
                self.ui.table.setItem(i, 4, QTableWidgetItem(r.get("voi", "")))
            self.ui.table.resizeRowsToContents()
            self.current_project_file = path
            self.ui.setWindowTitle(f"Project: {os.path.basename(path)}")
            QMessageBox.information(self.ui, "Thành công", "Đã tải dự án!")
        except Exception as e: QMessageBox.critical(self.ui, "Lỗi", str(e))