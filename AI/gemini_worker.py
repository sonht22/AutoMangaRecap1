import time
from google import genai
from PyQt6.QtCore import QThread, pyqtSignal

class GeminiScriptGenerator(QThread):
    update_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    # 1. Thêm tham số 'custom_style' vào hàm khởi tạo
    def __init__(self, api_key, data_list, custom_style=""):
        super().__init__()
        self.api_key = api_key
        self.data_list = data_list
        self.custom_style = custom_style # Lưu yêu cầu của bạn lại
        self.is_running = True
        
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            self.client = None
        
        self.model_name = "gemini-flash-latest"

    def run(self):
        if not self.client:
            self.error_signal.emit("Lỗi Client AI.")
            return

        print(f"🚀 AI chạy với style: {self.custom_style}")

        for row_index, text_input in self.data_list:
            if not self.is_running: break
            if not text_input.strip(): continue

            # 2. Cập nhật PROMPT để nhét yêu cầu của bạn vào
            # Nếu bạn không nhập gì, nó sẽ dùng mặc định là "Hấp dẫn, tự nhiên"
            style_instruction = self.custom_style if self.custom_style else "Hấp dẫn, tự nhiên, kể chuyện lôi cuốn."

            prompt = f"""
            Vai trò: Bạn là biên kịch video tóm tắt truyện tranh (Manga/Manhwa).
            
            Yêu cầu phong cách: {style_instruction}
            
            Nhiệm vụ: Dựa vào nội dung gốc dưới đây, hãy viết lại thành 1 câu lời bình (narration) ngôi thứ 3.
            Nội dung gốc: "{text_input}"
            
            Lưu ý: Chỉ trả về text kết quả đã viết lại. Không giải thích.
            """

            # --- Phần gọi API giữ nguyên ---
            max_retries = 3
            for attempt in range(max_retries):
                if not self.is_running: break
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                    
                    if response.text:
                        self.update_signal.emit(row_index, response.text.strip())
                    else:
                        self.update_signal.emit(row_index, "...")
                    
                    time.sleep(2) 
                    break 
                except Exception as e:
                    # (Giữ nguyên logic xử lý lỗi 429 cũ của bạn ở đây)
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        wait_time = 35
                        self.update_signal.emit(row_index, f"⏳ Đợi {wait_time}s...")
                        for _ in range(wait_time):
                            if not self.is_running: break
                            time.sleep(1)
                        continue
                    else:
                        self.update_signal.emit(row_index, "Lỗi API")
                        break
        self.finished_signal.emit()

    def stop(self):
        self.is_running = False