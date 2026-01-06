import sys
import os
import traceback

# Thêm đường dẫn hiện tại vào hệ thống để Python nhìn thấy folder AI
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print(f"📂 Đang kiểm tra import từ: {current_dir}")
print("-" * 50)

try:
    # Cố gắng import file worker
    from AI import gemini_worker
    print("✅ THÀNH CÔNG: Import được 'gemini_worker'. File này không có lỗi cú pháp.")
    
    # Kiểm tra xem class có tồn tại không
    if hasattr(gemini_worker, 'GeminiScriptGenerator'):
        print("✅ THÀNH CÔNG: Tìm thấy class 'GeminiScriptGenerator'.")
    else:
        print("❌ LỖI LOGIC: Không tìm thấy class 'GeminiScriptGenerator' trong file.")

except ImportError as e:
    print("❌ LỖI IMPORT (Python không thấy file):")
    print(e)
except SyntaxError as e:
    print("❌ LỖI CÚ PHÁP (Code trong file gemini_worker.py viết sai):")
    print(e)
    traceback.print_exc()
except Exception as e:
    print("❌ LỖI KHÁC:")
    print(e)
    traceback.print_exc()

print("-" * 50)
input("Nhấn Enter để thoát...")