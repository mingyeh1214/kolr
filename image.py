"""
Instagram 頁面截圖爬蟲
讀取 link.csv，對未完成的 Instagram 頁面進行長截圖
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import os
import re
from PIL import Image
import io


def setup_driver():
    """設定 Chrome WebDriver"""
    chrome_options = Options()
    # 取消註解下面這行可以讓瀏覽器在背景執行（無頭模式）
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 設定 user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 使用 webdriver-manager 自動管理 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def extract_username_from_url(url):
    """從 Instagram URL 中提取帳號名稱"""
    try:
        # 移除尾部的斜線
        url = url.rstrip('/')
        # 使用正則表達式提取帳號名稱
        match = re.search(r'instagram\.com/([^/?]+)', url)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"提取帳號名稱時發生錯誤: {e}")
        return None


def wait_for_page_load(driver, wait_time=2):
    """等待頁面內容載入完成"""
    try:
        # 等待頁面載入狀態
        ready_state = driver.execute_script("return document.readyState")
        if ready_state != "complete":
            time.sleep(wait_time)
        
        # 等待基本時間，讓內容載入
        time.sleep(wait_time)
        
        # 檢查可見區域內的圖片載入狀態
        try:
            images_loaded = driver.execute_script("""
                let images = document.querySelectorAll('img');
                let viewportHeight = window.innerHeight;
                let scrollTop = window.pageYOffset;
                let loadedCount = 0;
                let visibleCount = 0;
                
                for (let img of images) {
                    let rect = img.getBoundingClientRect();
                    let imgTop = rect.top + scrollTop;
                    let imgBottom = rect.bottom + scrollTop;
                    
                    if (imgBottom >= scrollTop - 200 && imgTop <= scrollTop + viewportHeight + 200) {
                        visibleCount++;
                        if (img.complete && img.naturalWidth > 0) {
                            loadedCount++;
                        }
                    }
                }
                
                return visibleCount > 0 ? (loadedCount / visibleCount) : 1;
            """)
            
            # 如果載入比例低於 80%，再等待一下
            if images_loaded < 0.8:
                time.sleep(1)
        except:
            # 如果檢查失敗，繼續執行
            pass
        
    except Exception as e:
        # 如果檢查失敗，至少等待基本時間
        time.sleep(wait_time)


def take_full_page_screenshot(driver, save_path):
    """進行長截圖（全頁面截圖）"""
    try:
        # 確保視窗最大化
        print("最大化瀏覽器視窗...")
        driver.maximize_window()
        time.sleep(1)  # 等待視窗最大化完成
        
        # 初始等待，讓頁面基本內容載入
        print("等待頁面初始載入...")
        time.sleep(2)
        
        # 獲取頁面總高度和寬度（最大化後的尺寸）
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        viewport_width = driver.execute_script("return window.innerWidth")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # 確保視窗保持最大化狀態
        driver.maximize_window()
        
        # 再次等待，確保視窗大小調整後內容重新計算
        time.sleep(1)
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        
        # 如果頁面高度小於視窗高度，直接截圖
        if total_height <= viewport_height:
            wait_for_page_load(driver, wait_time=2)
            driver.save_screenshot(save_path)
            return True
        
        # 需要滾動截圖並合併（最多5張，增加截圖數量）
        max_screenshots = 5  # 增加截圖數量限制
        screenshots = []
        scroll_position = 0
        
        # 滾動到頂部開始
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        while scroll_position < total_height and len(screenshots) < max_screenshots:
            # 平滑滾動到當前位置
            driver.execute_script(f"window.scrollTo({{ top: {scroll_position}, behavior: 'smooth' }});")
            time.sleep(1)  # 等待滾動動畫完成
            
            # 等待頁面內容載入（特別是 Instagram 的懶加載圖片）
            wait_for_page_load(driver, wait_time=2)
            
            # 額外等待，確保動態內容載入
            time.sleep(1.5)
            
            # 檢查滾動位置是否穩定
            current_scroll = driver.execute_script("return window.pageYOffset;")
            if abs(current_scroll - scroll_position) > 50:
                # 如果滾動位置差異太大，重新滾動
                driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(1.5)
            
            # 截圖
            screenshot = driver.get_screenshot_as_png()
            screenshots.append(screenshot)
            print(f"已截取第 {len(screenshots)} 張截圖（位置: {scroll_position}px）")
            
            # 更新滾動位置（使用視窗高度的 90% 來避免重疊）
            scroll_position += int(viewport_height * 0.9)
            
            # 如果已經到達底部，停止
            current_bottom = driver.execute_script("return window.pageYOffset + window.innerHeight;")
            if current_bottom >= total_height - 20:  # 20px 的容差
                print("已到達頁面底部")
                break
        
        # 滾動回頂部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # 合併截圖
        if len(screenshots) == 1:
            with open(save_path, 'wb') as f:
                f.write(screenshots[0])
        else:
            # 只取前 max_screenshots 張截圖
            screenshots = screenshots[:max_screenshots]
            images = [Image.open(io.BytesIO(img)) for img in screenshots]
            total_width = max(img.width for img in images)
            
            # 計算總高度（簡單拼接，保留所有內容）
            # 由於使用 90% 視窗高度滾動，會有少量重疊，但保留所有內容更安全
            merged_height = sum(img.height for img in images)
            
            merged_image = Image.new('RGB', (total_width, merged_height))
            y_offset = 0
            
            for img in images:
                merged_image.paste(img, (0, y_offset))
                y_offset += img.height
            
            merged_image.save(save_path)
            
            if len(screenshots) >= max_screenshots:
                print(f"注意：頁面過長，只截取了前 {max_screenshots} 張截圖")
        
        return True
    except Exception as e:
        print(f"截圖時發生錯誤: {e}")
        # 如果長截圖失敗，嘗試簡單截圖
        try:
            driver.save_screenshot(save_path)
            print("已使用簡單截圖作為備用方案")
            return True
        except Exception as e2:
            print(f"簡單截圖也失敗: {e2}")
            return False


def update_csv_image_done(csv_filename, url, status="true"):
    """更新 CSV 檔案中指定 URL 的 image_done 欄位"""
    try:
        # 讀取所有資料
        rows = []
        url_found = False
        with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            if headers is None:
                return False
            
            rows.append(headers)
            for row in reader:
                if len(row) > 0:
                    row_url = row[0].strip().strip('"')  # 移除可能的引號和空白
                    if row_url == url.strip().strip('"'):
                        # 更新 image_done 欄位
                        if len(row) > 1:
                            row[1] = status
                        else:
                            row.append(status)
                        url_found = True
                rows.append(row)
        
        if not url_found:
            print(f"警告：在 CSV 中找不到 URL: {url}")
            return False
        
        # 寫回檔案
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
        
        return True
    except Exception as e:
        print(f"更新 CSV 時發生錯誤: {e}")
        return False


def screenshot_instagram_pages(csv_filename='link.csv', image_folder='image'):
    """讀取 CSV 檔案，對未完成的 Instagram 頁面進行截圖"""
    # 建立 image 資料夾
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        print(f"已建立資料夾: {image_folder}")
    
    # 讀取 CSV 檔案
    if not os.path.exists(csv_filename):
        print(f"錯誤：找不到 CSV 檔案 {csv_filename}")
        return
    
    # 初始化 driver
    driver = setup_driver()
    
    try:
        # 開啟 Instagram 首頁並等待使用者登入
        print("\n" + "="*50)
        print("正在開啟 Instagram 首頁...")
        print("="*50)
        driver.get("https://www.instagram.com/")
        
        # 儲存第一個 tab 的 window handle（登入用的 tab）
        first_tab_handle = driver.current_window_handle
        
        print("\n請在 120 秒內手動登入 Instagram...")
        print("登入完成後，程式將自動開始截圖任務")
        time.sleep(120)
        print("\n登入等待時間結束，開始處理截圖任務...")
        
        # 讀取 CSV 並處理每一筆資料
        with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            
            if headers is None or len(headers) < 2:
                print("錯誤：CSV 檔案格式不正確")
                return
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for row in reader:
                if not row or len(row) == 0 or not row[0]:
                    continue
                
                url = row[0].strip().strip('"')  # 移除可能的引號
                image_done = row[1].strip().strip('"').lower() if len(row) > 1 else ""
                
                # 檢查是否已完成（如果 image_done 是 "true" 則跳過）
                if image_done == "true":
                    skipped_count += 1
                    print(f"\n跳過已完成: {url}")
                    continue
                
                # 提取帳號名稱
                username = extract_username_from_url(url)
                if not username:
                    print(f"\n無法從 URL 提取帳號名稱: {url}")
                    error_count += 1
                    continue
                
                print(f"\n{'='*50}")
                print(f"處理: {url}")
                print(f"帳號名稱: {username}")
                print(f"{'='*50}")
                
                try:
                    # 開啟新 tab
                    print(f"正在開啟新分頁...")
                    driver.switch_to.new_window('tab')
                    new_tab_handle = driver.current_window_handle
                    
                    # 在新 tab 中開啟頁面
                    print(f"正在開啟頁面...")
                    driver.get(url)
                    time.sleep(5)  # 等待頁面載入
                    
                    # 進行長截圖
                    image_path = os.path.join(image_folder, f"{username}.png")
                    print(f"正在截圖...")
                    
                    success = take_full_page_screenshot(driver, image_path)
                    
                    if success:
                        print(f"截圖已儲存: {image_path}")
                        
                        # 更新 CSV
                        if update_csv_image_done(csv_filename, url, "true"):
                            print(f"已更新 CSV: image_done = true")
                            processed_count += 1
                        else:
                            print(f"警告：無法更新 CSV")
                            error_count += 1
                    else:
                        print(f"截圖失敗")
                        error_count += 1
                    
                    # 先切換回第一個 tab（登入用的 tab），再關閉新 tab
                    print(f"正在切換回第一個分頁...")
                    try:
                        driver.switch_to.window(first_tab_handle)
                    except Exception as switch_error:
                        print(f"切換到第一個分頁時發生錯誤: {switch_error}")
                    
                    # 關閉新開啟的 tab（確保不會關閉最後一個 tab）
                    print(f"正在關閉分頁...")
                    try:
                        # 檢查是否還有其他 tab
                        all_handles = driver.window_handles
                        if len(all_handles) > 1 and new_tab_handle in all_handles:
                            driver.switch_to.window(new_tab_handle)
                            driver.close()
                            # 再次確保切換回第一個 tab
                            driver.switch_to.window(first_tab_handle)
                    except Exception as close_error:
                        print(f"關閉分頁時發生錯誤: {close_error}")
                        # 如果關閉失敗，確保切換回第一個 tab
                        try:
                            driver.switch_to.window(first_tab_handle)
                        except:
                            pass
                    
                    # 短暫延遲，避免請求過快
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"處理 {url} 時發生錯誤: {e}")
                    # 確保切換回第一個 tab，並關閉可能開啟的新 tab
                    try:
                        # 獲取所有 window handles
                        all_handles = driver.window_handles
                        # 如果有多個 tab，關閉非第一個 tab
                        if len(all_handles) > 1:
                            for handle in all_handles:
                                if handle != first_tab_handle:
                                    try:
                                        driver.switch_to.window(handle)
                                        driver.close()
                                    except:
                                        pass
                        # 切換回第一個 tab
                        driver.switch_to.window(first_tab_handle)
                    except Exception as switch_error:
                        print(f"切換分頁時發生錯誤: {switch_error}")
                    error_count += 1
                    continue
        
        print(f"\n{'='*50}")
        print(f"截圖任務完成！")
        print(f"成功處理: {processed_count} 筆")
        print(f"跳過: {skipped_count} 筆")
        print(f"錯誤: {error_count} 筆")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"讀取 CSV 時發生錯誤: {e}")
    finally:
        if driver:
            driver.quit()
            print("瀏覽器已關閉")


def main():
    """主函數"""
    csv_filename = 'link.csv'
    image_folder = 'image'
    
    print("開始 Instagram 頁面截圖任務...")
    screenshot_instagram_pages(csv_filename, image_folder)


if __name__ == "__main__":
    main()
