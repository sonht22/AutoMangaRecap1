import os
import sys

def check_project_structure():
    print("="*40)
    print("   KIỂM TRA CẤU TRÚC DỰ ÁN")
    print("="*40)

    current_dir = os.getcwd()
    print(f"📂 Thư mục đang chạy: {current_dir}")

    # 1. Kiểm tra file .env
    env_path = os.path.join(current_dir, ".env")
    if os.path.exists(env_path):
        print("✅ [OK] Đã tìm thấy file .env")
        # Check nội dung sơ bộ
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "GEMINI_API_KEY=" in content:
                    print("   -> Nội dung có vẻ đúng (Có chứa GEMINI_API_KEY).")
                else:
                    print("   ❌ [CẢNH BÁO] File .env không chứa dòng 'GEMINI_API_KEY='.")
        except:
            print("   ❌ Không đọc được file .env")
    else:
        print("❌ [LỖI] Không tìm thấy file .env (Hãy tạo nó ngay cạnh main.py)")

    # 2. Kiểm tra folder AI
    ai_dir = os.path.join(current_dir, "AI")
    if os.path.exists(ai_dir) and os.path.isdir(ai_dir):
        print("✅ [OK] Đã tìm thấy folder 'AI'")
        
        # 3. Kiểm tra __init__.py
        init_file = os.path.join(ai_dir, "__init__.py")
        if os.path.exists(init_file):
            print("✅ [OK] Đã tìm thấy file 'AI/__init__.py'")
        else:
            print("❌ [LỖI] Thiếu file 'AI/__init__.py'. Hãy tạo file rỗng tên này.")

        # 4. Kiểm tra gemini_worker.py
        worker_file = os.path.join(ai_dir, "gemini_worker.py")
        if os.path.exists(worker_file):
            print("✅ [OK] Đã tìm thấy file 'AI/gemini_worker.py'")
        else:
            print("❌ [LỖI] Không tìm thấy 'AI/gemini_worker.py'. Kiểm tra lại tên file.")
            
    else:
        print("❌ [LỖI] Không tìm thấy folder 'AI'.")

    print("="*40)

if __name__ == "__main__":
    check_project_structure()
    input("Nhấn Enter để thoát...")