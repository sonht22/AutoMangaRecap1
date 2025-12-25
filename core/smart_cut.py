# file: core/smart_cut.py
import cv2
import numpy as np
import os

def analyze_panels_coordinates(image_path, threshold_val=240, min_height=100):
    """
    Phân tích ảnh và trả về danh sách tọa độ (x, y, w, h).
    """
    if not os.path.exists(image_path):
        return [], None

    # Đọc ảnh (Hỗ trợ đường dẫn tiếng Việt)
    try:
        stream = open(image_path, "rb")
        bytes_data = bytearray(stream.read())
        numpy_array = np.asarray(bytes_data, dtype=np.uint8)
        img = cv2.imdecode(numpy_array, cv2.IMREAD_UNCHANGED)
    except Exception as e:
        print(f"Lỗi đọc ảnh: {e}")
        return [], None
    
    if img is None:
        return [], None
    
    # Xử lý kênh Alpha (PNG trong suốt)
    if len(img.shape) == 3 and img.shape[2] == 4:
        trans_mask = img[:, :, 3] == 0
        img[trans_mask] = [255, 255, 255, 255]
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif len(img.shape) == 2: # Ảnh xám
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    h_img, w_img = img.shape[:2]
    
    # Chuyển xám và nhị phân
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY_INV)
    
    # Chiếu ngang
    projection = np.sum(binary, axis=1)
    
    segments = []
    start = -1
    
    for y, val in enumerate(projection):
        if val > 0: 
            if start == -1: start = y
        else:
            if start != -1:
                if (y - start) > min_height:
                    segments.append([start, y])
                start = -1
                
    if start != -1 and (h_img - start) > min_height:
        segments.append([start, h_img])

    # FIX LỖI: Panel đầu tiên sát mép trên
    if len(segments) > 0 and segments[0][0] < 100:
        segments[0][0] = 0

    # Chuyển đổi sang format (x, y, w, h)
    rects = []
    for (y1, y2) in segments:
        rects.append((0, y1, w_img, y2 - y1))
        
    return rects, img

def save_cropped_images(original_img, rects, output_folder, file_prefix="panel"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    saved_paths = []
    for i, (x, y, w, h) in enumerate(rects):
        if w <= 0 or h <= 0: continue
        
        # Kiểm tra biên an toàn
        h_img, w_img = original_img.shape[:2]
        x = max(0, min(x, w_img)); y = max(0, min(y, h_img))
        w = min(w, w_img - x); h = min(h, h_img - y)
        
        crop = original_img[y:y+h, x:x+w]
        
        if crop.size > 0:
            filename = f"{file_prefix}_{i+1:04d}.jpg"
            path = os.path.join(output_folder, filename)
            is_success, im_buf_arr = cv2.imencode(".jpg", crop)
            if is_success:
                im_buf_arr.tofile(path)
                saved_paths.append(path)
                
    return saved_paths