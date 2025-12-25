import os
import shutil
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem, QListWidgetItem, QProgressDialog
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

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
        self.ui.image_list.clear()
        if not self.current_folder: return
        if os.path.exists(self.current_folder):
            files = sorted([f for f in os.listdir(self.current_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))])
            self.is_renaming = True
            for f in files:
                item = QListWidgetItem(f)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, f)
                self.ui.image_list.addItem(item)
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
                if old_name in self.cached_rects:
                    self.cached_rects[new_name] = self.cached_rects.pop(old_name)
                self.is_renaming = True
                item.setData(Qt.ItemDataRole.UserRole, new_name)
                self.is_renaming = False
                if self.current_file_path == old_path:
                    self.current_file_path = new_path
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