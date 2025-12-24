import os
import shutil
import re # Thư viện để tìm số trong chuỗi (cho tính năng sắp xếp)
from PyQt6.QtWidgets import QFileDialog, QListWidgetItem, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

# Import module cắt ảnh
from core.smart_cut import SmartCutter 

class AppLogic:
    def __init__(self, main_window):
        # Lưu tham chiếu đến giao diện chính
        self.mw = main_window 
        self.current_folder = ""
        self.is_loading = False # Cờ hiệu để tránh xung đột khi đang load dữ liệu

    # =======================================================
    # 1. QUẢN LÝ FILE & FOLDER
    # =======================================================
    def action_load_folder(self):
        folder = QFileDialog.getExistingDirectory(self.mw, "Chọn thư mục")
        if folder:
            self.load_images_to_ui(folder)

    def load_images_to_ui(self, folder_path):
        self.current_folder = folder_path
        self.mw.image_list.clear()
        self.is_loading = True # Bật cờ đang load
        
        self.mw.setWindowTitle(f"Auto Manga Recap - {os.path.basename(folder_path)}")
        
        # Lấy danh sách ảnh
        files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        self.mw.table.setRowCount(len(files))
        
        for i, f in enumerate(files):
            # Tạo Item cho danh sách bên trái
            item = QListWidgetItem(f)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable) # Cho phép sửa tên
            item.setData(Qt.ItemDataRole.UserRole, f) # Lưu tên gốc vào bộ nhớ ẩn
            self.mw.image_list.addItem(item)
            
            # Tạo dòng cho bảng bên phải
            self.mw.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.mw.table.setItem(i, 1, QTableWidgetItem(f))
            self.mw.table.setItem(i, 2, QTableWidgetItem(""))
            self.mw.table.setItem(i, 3, QTableWidgetItem(""))
            
        self.is_loading = False # Tắt cờ load
        print(f"✅ Đã load {len(files)} ảnh từ: {folder_path}")

    def display_image(self, row_index):
        if row_index < 0: return
        file_name = self.mw.image_list.item(row_index).text()
        full_path = os.path.join(self.current_folder, file_name)
        
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                self.mw.viewer.set_photo(pixmap)

    # =======================================================
    # 2. ĐỔI TÊN FILE (RENAME)
    # =======================================================
    def handle_rename_file(self, item):
        # Nếu đang load hoặc không có folder thì dừng
        if self.is_loading or not self.current_folder: return

        new_name = item.text().strip()
        old_name = item.data(Qt.ItemDataRole.UserRole)
        
        # Nếu tên không đổi -> Dừng
        if not old_name or new_name == old_name:
            return

        print(f"✏️ Đang đổi tên: '{old_name}' -> '{new_name}'")

        # KHÓA GIAO DIỆN (Để tránh vòng lặp vô hạn)
        self.mw.image_list.blockSignals(True)

        try:
            # Tự động thêm đuôi file nếu thiếu (vd: .jpg)
            _, ext = os.path.splitext(old_name)
            if not new_name.lower().endswith(ext.lower()):
                new_name += ext
            
            old_path = os.path.join(self.current_folder, old_name)
            new_path = os.path.join(self.current_folder, new_name)

            # Đổi tên file thật trên ổ cứng
            os.rename(old_path, new_path)
            print("✅ Đổi tên thành công!")

            # Cập nhật lại giao diện và bộ nhớ ẩn
            item.setText(new_name)
            item.setData(Qt.ItemDataRole.UserRole, new_name)
            
            # Đồng bộ sang bảng bên phải
            self._sync_table_internal()

        except OSError as e:
            print(f"❌ Lỗi đổi tên: {e}")
            item.setText(old_name) # Trả về tên cũ nếu lỗi
            QMessageBox.warning(self.mw, "Lỗi", f"Không thể đổi tên!\n{e}")

        finally:
            # MỞ KHÓA GIAO DIỆN
            self.mw.image_list.blockSignals(False)

    # =======================================================
    # 3. [NÂNG CẤP] SẮP XẾP & ĐỒNG BỘ FOLDER (AUTO SORT)
    # =======================================================
    def action_auto_sort(self):
        count = self.mw.image_list.count()
        if count == 0: return

        print("🔄 Đang sắp xếp danh sách...")
        
        # 1. Nhấc item ra và Sắp xếp (Natural Sort)
        items = []
        while self.mw.image_list.count() > 0:
            item = self.mw.image_list.takeItem(0)
            items.append(item)

        def natural_key(item):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', item.text())]

        items.sort(key=natural_key)

        # Đưa lại vào List Widget
        for item in items:
            self.mw.image_list.addItem(item)
        
        # --- [MỚI] ĐỒNG BỘ TÊN FILE TRONG FOLDER ---
        reply = QMessageBox.question(self.mw, "Đồng bộ Folder", 
                                     "Bạn có muốn ĐỔI TÊN tất cả file trong folder thành số thứ tự (001.jpg, 002.jpg...) \n"
                                     "để sắp xếp folder giống hệt trên App không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self._batch_rename_sequence(items)
        
        # Đồng bộ bảng
        self.sync_table_order()
        print("✅ Hoàn tất sắp xếp!")

    def _batch_rename_sequence(self, items):
        """Hàm đổi tên hàng loạt an toàn (2 bước)"""
        print("🚀 Bắt đầu đổi tên hàng loạt...")
        self.mw.image_list.blockSignals(True) # Khóa giao diện
        
        try:
            # Bước 1: Đổi sang tên tạm (temp_xxxx) để tránh trùng lặp
            # Ví dụ: Muốn đổi "2.jpg" thành "1.jpg", nhưng "1.jpg" đang tồn tại -> Phải đổi sang tên tạm trước.
            temp_map = [] # Lưu cặp (tên tạm, đuôi file)
            
            for i, item in enumerate(items):
                old_name = item.text() # Tên hiện tại (VD: 1.jpg)
                old_path = os.path.join(self.current_folder, old_name)
                
                _, ext = os.path.splitext(old_name)
                
                # Tạo tên tạm ngẫu nhiên hoặc theo số lớn
                temp_name = f"temp_recap_{i:04d}{ext}"
                temp_path = os.path.join(self.current_folder, temp_name)
                
                os.rename(old_path, temp_path)
                temp_map.append((temp_name, ext)) # Nhớ tên tạm và đuôi file
            
            # Bước 2: Đổi từ tên tạm sang tên chuẩn (001.jpg, 002.jpg...)
            for i, (temp_name, ext) in enumerate(temp_map):
                new_name = f"{i+1:03d}{ext}" # VD: 001.jpg
                
                temp_path = os.path.join(self.current_folder, temp_name)
                new_path = os.path.join(self.current_folder, new_name)
                
                os.rename(temp_path, new_path)
                
                # Cập nhật lại tên trên giao diện App
                items[i].setText(new_name)
                items[i].setData(Qt.ItemDataRole.UserRole, new_name)
            
            print("✅ Đã đổi tên toàn bộ file trong folder!")
            QMessageBox.information(self.mw, "Thành công", "Đã đổi tên và sắp xếp folder xong!")
            
        except Exception as e:
            print(f"❌ Lỗi khi đổi tên hàng loạt: {e}")
            QMessageBox.critical(self.mw, "Lỗi", f"Có lỗi xảy ra khi đổi tên: {e}")
            # Nếu lỗi, nên load lại folder để đảm bảo hiển thị đúng
            self.load_images_to_ui(self.current_folder)
            
        finally:
            self.mw.image_list.blockSignals(False)

    # =======================================================
    # 4. CẮT ẢNH (SMART CUT)
    # =======================================================
    # ... (Trong file ui/app_logic.py) ...

    def action_smart_cut(self):
        if not self.current_folder:
            QMessageBox.warning(self.mw, "Lỗi", "Chưa chọn folder!")
            return

        # [MỚI] Lấy thông số Adjustment từ giao diện PanelDock
        w_adj = self.mw.panel_dock.spin_width_adj.value()
        h_adj = self.mw.panel_dock.spin_height_adj.value()

        reply = QMessageBox.question(self.mw, "Cắt Ảnh", 
                                     f"Cắt với thông số điều chỉnh:\nWidth: {w_adj}px\nHeight: {h_adj}px\n\n"
                                     "Tiếp tục?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No: return

        output_folder = os.path.join(self.current_folder, "cut_panels")
        if os.path.exists(output_folder): shutil.rmtree(output_folder)
        os.makedirs(output_folder)

        cutter = SmartCutter()
        total_panels = 0
        count = self.mw.image_list.count()

        if count == 0: return

        self.mw.image_list.blockSignals(True)
        self.mw.setWindowTitle("⏳ Đang cắt ảnh (Advanced Mode)...")

        try:
            for i in range(count):
                file_name = self.mw.image_list.item(i).text()
                img_path = os.path.join(self.current_folder, file_name)
                
                # [QUAN TRỌNG] Truyền w_adj và h_adj vào
                num = cutter.process_image(img_path, output_folder, total_panels + 1, 
                                           w_adj=w_adj, 
                                           h_adj=h_adj)
                
                total_panels += num
                print(f"-> Cắt {file_name}: {num} khung")
                
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()

            QMessageBox.information(self.mw, "Xong", f"Đã cắt được {total_panels} khung tranh!")
            self.load_images_to_ui(output_folder)

        except Exception as e:
            QMessageBox.critical(self.mw, "Lỗi", str(e))
        
        finally:
            self.mw.image_list.blockSignals(False)
            self.mw.setWindowTitle(f"Auto Manga Recap - {os.path.basename(self.current_folder)}")

    # =======================================================
    # 5. ĐỒNG BỘ BẢNG (SYNC)
    # =======================================================
    def sync_table_order(self):
        """Hàm gọi từ bên ngoài (khi kéo thả)"""
        self._sync_table_internal()

    def _sync_table_internal(self):
        """Hàm nội bộ để vẽ lại bảng bên phải dựa theo list bên trái"""
        if self.is_loading: return
        
        self.mw.table.blockSignals(True)
        self.mw.table.setUpdatesEnabled(False)
        try:
            # Lưu script cũ
            old_data = {}
            for row in range(self.mw.table.rowCount()):
                item_name = self.mw.table.item(row, 1)
                item_script = self.mw.table.item(row, 2)
                if item_name:
                    filename = item_name.text()
                    script = item_script.text() if item_script else ""
                    old_data[filename] = script

            # Vẽ lại bảng
            count = self.mw.image_list.count()
            self.mw.table.setRowCount(count)

            for i in range(count):
                file_name = self.mw.image_list.item(i).text()
                
                self.mw.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.mw.table.setItem(i, 1, QTableWidgetItem(file_name))
                
                script_text = old_data.get(file_name, "")
                self.mw.table.setItem(i, 2, QTableWidgetItem(script_text))
                self.mw.table.setItem(i, 3, QTableWidgetItem(""))
        except Exception: pass
        self.mw.table.setUpdatesEnabled(True)
        self.mw.table.blockSignals(False)