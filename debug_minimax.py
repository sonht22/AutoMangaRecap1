import requests
import json
import time

# ================= CẤU HÌNH (ĐIỀN KEY CỦA BẠN VÀO ĐÂY) =================
API_KEY = "sk_lhmn5z2hwe5c8vmc34gddd66g6muma706dijdal4j6cmb1k9"  # <-- Dán API Key Minimax/AI33 của bạn vào đây
VOICE_ID = "262184394641600"         # ID giọng nói (Giọng nam trầm/thuyết minh)
TEXT_DEMO = "Xin chào, đây là đoạn âm thanh thử nghiệm để kiểm tra hệ thống recap truyện."

# Các Endpoint (Dựa trên tài liệu phổ biến của AI33/Minimax)
URL_CREATE = "https://api.ai33.pro/v1m/task/text-to-speech"
URL_QUERY  = "https://api.ai33.pro/v1m/task/query" 

# Headers chung
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "RecapTool/1.0"
}

def debug_minimax_flow():
    print("\n" + "="*50)
    print("   BẮT ĐẦU DEBUG KẾT NỐI MINIMAX (AI33.PRO)")
    print("="*50 + "\n")

    # -----------------------------------------------------------
    # BƯỚC 1: GỬI YÊU CẦU TẠO AUDIO (CREATE TASK)
    # -----------------------------------------------------------
    print("[BƯỚC 1] Gửi yêu cầu tạo giọng nói...")
    
    payload_create = {
        "model": "speech-01",     # Tên model (có thể thay đổi tùy gói)
        "voice_id": VOICE_ID,
        "text": TEXT_DEMO,
        "speed": 1.0,
        "vol": 1.0
    }

    try:
        response = requests.post(URL_CREATE, headers=headers, json=payload_create, timeout=30)
        
        # In Status Code
        print(f"Status Code: {response.status_code}")

        # Xử lý nếu Server lỗi (5xx, 4xx)
        if response.status_code != 200:
            print("❌ LỖI KẾT NỐI (Create Task):")
            print(f"Nội dung phản hồi: {response.text}")
            return

        # Parse JSON
        data = response.json()
        print(f"Response Raw: {json.dumps(data, ensure_ascii=False)}")

        # Lấy Task ID
        if data.get("success") is True or data.get("code") == 1000: # Check tùy cấu trúc API trả về
            task_id = data.get("task_id")
            if not task_id:
                # Một số API trả về thẳng audio url luôn mà không cần polling
                if "audio_url" in data.get("data", {}):
                    print(f"✅ CÓ AUDIO LUÔN (Không cần polling): {data['data']['audio_url']}")
                    return
                print("❌ Không tìm thấy task_id trong phản hồi thành công.")
                return
                
            print(f"✅ TẠO TASK THÀNH CÔNG! Task ID: {task_id}")
        else:
            print(f"❌ API báo lỗi logic: {data.get("msg") or data}")
            return

    except Exception as e:
        print(f"❌ LỖI NGOẠI LỆ (Create): {e}")
        return

    # -----------------------------------------------------------
    # BƯỚC 2: POLLING (HỎI SERVER XEM XONG CHƯA)
    # -----------------------------------------------------------
    print("\n[BƯỚC 2] Bắt đầu Polling (Chờ xử lý)...")
    
    payload_query = {
        "task_id": task_id
    }

    retry_count = 0
    max_retries = 10  # Thử tối đa 10 lần (20 giây)

    while retry_count < max_retries:
        time.sleep(2) # Đợi 2s mỗi lần hỏi
        retry_count += 1
        print(f"   >>> Đang hỏi lần {retry_count}/{max_retries}...")

        try:
            # Gửi request kiểm tra
            resp_query = requests.post(URL_QUERY, headers=headers, json=payload_query, timeout=10)
            
            # --- KHẮC PHỤC LỖI "Expecting value" TẠI ĐÂY ---
            # 1. Kiểm tra status code trước
            if resp_query.status_code != 200:
                print(f"   ❌ Lỗi Server khi Polling: {resp_query.status_code}")
                print(f"   Nội dung trả về: {resp_query.text}") # In ra xem nó là HTML hay gì
                break
            
            # 2. Thử decode JSON an toàn
            try:
                data_query = resp_query.json()
            except json.JSONDecodeError:
                print("   ❌ LỖI: Server không trả về JSON hợp lệ.")
                print(f"   Raw Text nhận được: '{resp_query.text}'")
                break
            # ------------------------------------------------

            # 3. Kiểm tra trạng thái trong JSON
            # Cấu trúc JSON thường gặp: {"success": true, "data": {"status": "success", "audio_url": "..."}}
            is_success = data_query.get("success")
            status_task = data_query.get("data", {}).get("status") # Có thể là "queued", "processing", "success", "failed"

            if is_success and status_task == "success":
                audio_url = data_query.get("data", {}).get("audio_url")
                print("\n" + "="*50)
                print("✅ THÀNH CÔNG! FILE AUDIO CỦA BẠN:")
                print(audio_url)
                print("="*50)
                
                # Tự động tải về file test.mp3
                print("⬇️ Đang tải xuống file 'test_recap.mp3'...")
                audio_content = requests.get(audio_url).content
                with open("test_recap.mp3", "wb") as f:
                    f.write(audio_content)
                print("✅ Đã lưu file: test_recap.mp3")
                break
            
            elif status_task == "failed":
                print(f"❌ Task thất bại: {data_query}")
                break
            else:
                # Nếu đang processing hoặc queued
                print(f"   ⏳ Trạng thái: {status_task} - Đang đợi...")

        except Exception as e:
            print(f"   ❌ Lỗi kết nối khi polling: {e}")
            break
    else:
        print("❌ Hết thời gian chờ (Timeout). Server xử lý quá lâu.")

if __name__ == "__main__":
    debug_minimax_flow()