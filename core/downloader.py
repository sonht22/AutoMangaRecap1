import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

class ChapterDownloader:
    def __init__(self):
        # Cấu hình Chrome để chạy ngầm (Headless) hoặc hiện (để debug)
        self.chrome_options = Options()
        # self.chrome_options.add_argument("--headless")  # Bỏ comment dòng này nếu muốn ẩn trình duyệt
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    def download_chapter(self, url, output_folder, merge_one_image=True):
        print(f"🌐 Đang khởi động Chrome để tải: {url}")
        
        # Tự động tải và cài driver Chrome phù hợp
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        
        try:
            # 1. Mở trang web
            driver.get(url)
            time.sleep(3) # Chờ web load cơ bản

            # 2. CUỘN TRANG TỪ TỪ (SCROLL) - QUAN TRỌNG NHẤT
            # Web truyện dùng Lazy-load, phải cuộn xuống thì ảnh mới hiện
            print("📜 Đang cuộn trang để load toàn bộ ảnh...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Cuộn xuống một chút
                driver.execute_script("window.scrollTo(0, window.scrollY + 800);")
                time.sleep(0.5) # Nghỉ chút để ảnh kịp load
                
                # Kiểm tra xem đã đến đáy chưa
                new_height = driver.execute_script("return window.scrollY + window.innerHeight")
                if new_height >= driver.execute_script("return document.body.scrollHeight"):
                    break
            
            print("✅ Đã cuộn xong. Đang quét ảnh...")
            time.sleep(2) # Chờ thêm chút cho chắc

            # 3. Lấy tất cả thẻ ảnh <img> thông qua Javascript
            # Cách này lấy được cả ảnh ẩn trong Shadow DOM hoặc Canvas
            images = driver.find_elements("tag name", "img")
            
            valid_img_links = []
            for img in images:
                # Lấy link từ mọi thuộc tính có thể
                src = img.get_attribute('src')
                data_src = img.get_attribute('data-src')
                data_original = img.get_attribute('data-original')
                
                link = data_original or data_src or src
                
                if not link: continue
                
                # LỌC RÁC (Logo, Icon, Quảng cáo...)
                if any(x in link for x in ['logo', 'icon', 'avatar', 'banner', 'facebook', 'google', 'ads', 'tracking']):
                    continue
                if link.endswith('.svg') or link.endswith('.gif'):
                    continue
                # Lọc ảnh quá bé (thường là icon ẩn)
                if img.size['width'] < 150 or img.size['height'] < 150:
                    continue

                if link not in valid_img_links:
                    valid_img_links.append(link)

            print(f"👀 Tìm thấy {len(valid_img_links)} ảnh truyện hợp lệ.")

            # 4. Tiến hành tải ảnh
            os.makedirs(output_folder, exist_ok=True)
            downloaded_paths = []

            # Dùng requests để tải file cho nhanh (không cần dùng selenium tải file)
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': url}
            
            for i, img_url in enumerate(valid_img_links):
                file_name = f"{i+1:03d}.jpg"
                save_path = os.path.join(output_folder, file_name)
                
                try:
                    # Tải file
                    response = requests.get(img_url, headers=headers, timeout=10)
                    if response.status_code == 200 and len(response.content) > 5000: # > 5KB mới lấy
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        downloaded_paths.append(save_path)
                        print(f"   -> Đã tải: {file_name}")
                    else:
                        print(f"   ⚠️ Lỗi hoặc ảnh rác: {img_url}")
                except Exception as e:
                    print(f"   ❌ Lỗi tải ảnh {i}: {e}")

            # 5. Gộp ảnh (Nếu cần)
            if merge_one_image and downloaded_paths:
                print("🔄 Đang gộp ảnh dài...")
                merged = self.merge_to_long_image(downloaded_paths, output_folder)
                if merged: return [merged]
            
            return downloaded_paths

        except Exception as e:
            print(f"❌ Lỗi Selenium: {e}")
            return None
        finally:
            driver.quit() # Tắt trình duyệt khi xong

    def merge_to_long_image(self, image_paths, output_folder):
        """Hàm nối ảnh (giữ nguyên như cũ)"""
        try:
            images = []
            for path in image_paths:
                try:
                    img = Image.open(path).convert('RGB')
                    images.append(img)
                except: pass
            
            if not images: return None

            max_width = max(img.width for img in images)
            total_height = 0
            resized_images = []
            
            for img in images:
                scale = max_width / img.width
                new_height = int(img.height * scale)
                resized_images.append(img.resize((max_width, new_height), Image.Resampling.LANCZOS))
                total_height += new_height

            long_image = Image.new('RGB', (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in resized_images:
                long_image.paste(img, (0, y_offset))
                y_offset += img.height

            save_path = os.path.join(output_folder, "full_chapter_merged.jpg")
            long_image.save(save_path, quality=85)
            return save_path
        except Exception as e:
            print(f"Lỗi gộp ảnh: {e}")
            return None