import cv2
import numpy as np
import os

def read_image_utf8(path):
    """
    Hàm đọc ảnh hỗ trợ đường dẫn tiếng Việt/Unicode trên Windows.
    Thay thế cho cv2.imread()
    """
    try:
        # Đọc file dưới dạng luồng dữ liệu (binary) -> Tránh lỗi tên file
        stream = open(path, "rb")
        bytes_data = bytearray(stream.read())
        numpy_array = np.asarray(bytes_data, dtype=np.uint8)
        # Giải mã luồng dữ liệu thành ảnh
        img = cv2.imdecode(numpy_array, cv2.IMREAD_UNCHANGED)
        return img
    except Exception as e:
        print(f"Lỗi đọc ảnh {path}: {e}")
        return None

def preprocess_image(image_path_or_array):
    """
    Hàm chuẩn hóa ảnh để tăng độ chính xác cho OCR.
    """
    img = None
    
    # 1. Đọc ảnh (Xử lý đường dẫn tiếng Việt)
    if isinstance(image_path_or_array, str):
        if not os.path.exists(image_path_or_array):
            print(f"File không tồn tại: {image_path_or_array}")
            return None
        img = read_image_utf8(image_path_or_array)
    else:
        # Nếu đầu vào là ảnh đã cắt sẵn (dạng numpy array)
        img = image_path_or_array

    if img is None:
        return None

    # Nếu ảnh có kênh Alpha (Trong suốt), chuyển nền thành trắng
    if len(img.shape) == 3 and img.shape[2] == 4:
        trans_mask = img[:,:,3] == 0
        img[trans_mask] = [255, 255, 255, 255]
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # 2. Phóng to ảnh lên 2 lần (Upscale)
    # Giúp các nét chữ nhỏ trở nên to rõ hơn, AI dễ bắt hơn
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # 3. Chuyển sang ảnh xám (Grayscale)
    # Kiểm tra xem ảnh có phải là ảnh màu không trước khi convert
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # 4. Tăng tương phản bằng Threshold (Phân ngưỡng)
    try:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    except:
        # Nếu lỗi threshold thì dùng ảnh xám gốc
        binary = gray

    # 5. Khử nhiễu (Denoise)
    try:
        denoised = cv2.fastNlMeansDenoising(binary, h=10, templateWindowSize=7, searchWindowSize=21)
        return denoised
    except:
        return binary