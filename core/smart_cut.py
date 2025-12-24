import cv2
import os
import numpy as np

class SmartCutter:
    def __init__(self):
        pass

    def read_image_safe(self, path):
        """Hàm đọc ảnh bất chấp tên folder tiếng Việt hay ký tự lạ"""
        try:
            stream = open(path, "rb")
            bytes_data = bytearray(stream.read())
            numpy_array = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_UNCHANGED)
            return img
        except Exception as e:
            print(f"❌ Không đọc được ảnh: {path}\nLỗi: {e}")
            return None

    def save_image_safe(self, img, path):
        """Hàm lưu ảnh an toàn với đường dẫn tiếng Việt"""
        try:
            _, ext = os.path.splitext(path)
            success, buffer = cv2.imencode(ext, img)
            if success:
                with open(path, "wb") as f:
                    f.write(buffer)
                return True
        except Exception as e:
            print(f"❌ Không lưu được ảnh: {path}\nLỗi: {e}")
        return False

    def process_image(self, img_path, output_folder, start_index, w_adj=0, h_adj=0, kernel_size=40, min_size=100):
        # 1. Đọc ảnh bằng hàm an toàn
        img = self.read_image_safe(img_path)
        
        if img is None:
            print(f"⚠️ Cảnh báo: File ảnh bị lỗi hoặc không tìm thấy: {img_path}")
            return 0
        
        # Nếu ảnh có kênh Alpha (trong suốt), chuyển về trắng
        if img.shape[2] == 4:
            trans_mask = img[:,:,3] == 0
            img[trans_mask] = [255, 255, 255, 255]
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        h_img, w_img = img.shape[:2]

        # 2. Xử lý ảnh: Chuyển xám -> Nhị phân hóa (Threshold)
        # Logic: Mọi thứ KHÔNG PHẢI MÀU TRẮNG (nền giấy) đều là nội dung
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Ngưỡng 240: Nghĩa là màu xám nhạt đến trắng tinh sẽ bị coi là nền. Còn lại là tranh.
        ret, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

        # 3. Gộp khối (Dilation)
        # Nở vùng màu trắng ra để các nét đứt nối lại với nhau
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size)) 
        dilated = cv2.dilate(thresh, kernel, iterations=2)

        # 4. Tìm viền (Contours)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sắp xếp từ Trên xuống Dưới
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

        valid_cuts = 0
        os.makedirs(output_folder, exist_ok=True)

        print(f"🔍 Tìm thấy {len(contours)} vùng có thể là tranh trong ảnh...")

        for c in contours:
            x, y, w, h = cv2.boundingRect(c)

            # --- LỌC RÁC ---
            # Chỉ bỏ qua nếu quá bé (nhỏ hơn min_size pixel)
            if w < min_size or h < min_size: 
                continue
            
            # --- ÁP DỤNG ADJUSTMENT (Chỉnh lề) ---
            new_x = x - w_adj
            new_y = y - h_adj
            new_w = w + (w_adj * 2)
            new_h = h + (h_adj * 2)

            # Giới hạn trong khung ảnh
            new_x = max(0, new_x)
            new_y = max(0, new_y)
            new_w = min(w_img - new_x, new_w)
            new_h = min(h_img - new_y, new_h)

            # Kiểm tra an toàn lần cuối
            if new_w <= 0 or new_h <= 0: continue

            # Cắt ảnh
            panel = img[new_y:new_y+new_h, new_x:new_x+new_w]

            save_name = f"panel_{start_index + valid_cuts:04d}.jpg"
            save_path = os.path.join(output_folder, save_name)
            
            # Lưu ảnh bằng hàm an toàn
            self.save_image_safe(panel, save_path)
            valid_cuts += 1
            
        return valid_cuts