import os

# Cấu trúc dự án
project_structure = {
    "core": [               # Chứa các file xử lý logic
        "smart_cut.py",     # Module cắt ảnh thông minh (OpenCV)
        "ai_writer.py",     # Module kết nối Gemini để viết nội dung
        "tts_engine.py",    # Module tạo giọng đọc
        "capcut_gen.py",    # Module xuất file CapCut
        "__init__.py"
    ],
    "ui": [                 # Chứa giao diện (Sau này sẽ viết)
        "main_window.py",
        "styles.qss"
    ],
    "assets": [],           # Chứa tài nguyên (icon, font...)
    "input_test": [],       # Nơi bạn copy thử 1 chap truyện vào để test
    "output": [],           # Nơi xuất kết quả
}

files_root = [
    "main.py",              # File chạy chính của chương trình
    ".env",                 # Nơi điền API Key (Bảo mật)
    "requirements.txt",     # Danh sách thư viện cần cài
    "README.md"             # Hướng dẫn sử dụng
]

def create_project():
    print("🚀 Đang khởi tạo dự án AutoMangaRecap...")
    
    # 1. Tạo các folder và file con
    for folder, files in project_structure.items():
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Đã tạo folder: /{folder}")
        
        for file in files:
            path = os.path.join(folder, file)
            if not os.path.exists(path):
                with open(path, 'w', encoding='utf-8') as f:
                    if file.endswith(".py"):
                        f.write(f"# Module: {file}\n# Viết code xử lý tại đây\n")
                print(f"   -> Đã tạo file: {file}")

    # 2. Tạo các file ở thư mục gốc
    for file in files_root:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                if file == "requirements.txt":
                    # Điền sẵn các thư viện cần thiết
                    f.write("opencv-python\nnumpy\ngoogle-generativeai\npython-dotenv\nPyQt6\nrequests\n")
                elif file == ".env":
                    f.write("GEMINI_API_KEY=Điền_Key_Của_Bạn_Vào_Đây\nTTS_API_KEY=Điền_Key_TTS_Vào_Đây")
            print(f"✅ Đã tạo file gốc: {file}")

    print("\n🎉 XONG! Cấu trúc dự án đã sẵn sàng.")
    print("👉 Bước tiếp theo: Mở Terminal và chạy lệnh: pip install -r requirements.txt")

if __name__ == "__main__":
    create_project()