"""
簡單的 KOLR.ai 爬蟲樣板
使用 Selenium 來開啟和處理動態網頁內容
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import os
import re
from urllib.parse import urlparse


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

def open_page(url, driver=None):
    """開啟指定的網頁"""
    if driver is None:
        driver = setup_driver()
    
    try:
        print(f"\n正在開啟頁面: {url}")
        driver.get(url)

        # 等待使用者手動登入
        print("請在 90 秒內手動登入...")
        time.sleep(90)
        
        # 手動登入後再重新進入 url
        print("再次載入頁面...")
        driver.get(url)
        
        print("等待頁面載入...")
        time.sleep(2)  # 給頁面一些時間載入
        
        print(f"頁面標題: {driver.title}")
        print(f"當前 URL: {driver.current_url}")
        
        return driver
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        if driver:
            driver.quit()
        return None


def get_page_info(driver):
    """獲取當前頁碼和總頁碼，返回 (current_page, total_pages)"""
    try:
        # 尋找包含頁碼資訊的 span 元素（格式：2 / 796 頁）
        # 這個 span 在 pagination_Wrapper-sc-1352b46e-1 bwXAuy 容器內
        page_info_elements = driver.find_elements(
            By.CSS_SELECTOR,
            "div.pagination_Wrapper-sc-1352b46e-1.bwXAuy span"
        )
        
        for element in page_info_elements:
            text = element.text.strip()
            # 匹配格式：數字 / 數字 頁
            match = re.search(r'(\d+)\s*/\s*(\d+)\s*頁', text)
            if match:
                current_page = int(match.group(1))
                total_pages = int(match.group(2))
                return current_page, total_pages
        
        # 如果找不到，嘗試其他可能的位置
        # 直接搜尋包含 "/" 和 "頁" 的文字
        all_spans = driver.find_elements(By.TAG_NAME, "span")
        for span in all_spans:
            text = span.text.strip()
            match = re.search(r'(\d+)\s*/\s*(\d+)\s*頁', text)
            if match:
                current_page = int(match.group(1))
                total_pages = int(match.group(2))
                return current_page, total_pages
        
        print("警告：無法找到頁碼資訊")
        return None, None
    except Exception as e:
        print(f"獲取頁碼資訊時發生錯誤: {e}")
        return None, None


def click_next_button(driver, max_wait_time=30):
    """點擊下一頁按鈕，返回是否成功。會等待按鈕可點擊（頁面載入完畢）"""
    try:
        # 等待按鈕出現，增加等待時間確保頁面載入完畢
        print("等待下一頁按鈕載入...")
        next_button = WebDriverWait(driver, max_wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-btn.css-var-r0.ant-btn-primary.pagination__PageButton-sc-1352b46e-0.hPROFu"))
        )
        
        # 檢查按鈕是否被禁用（最後一頁）
        if next_button.get_attribute("disabled"):
            print("已到達最後一頁（按鈕被禁用）")
            return False
        
        # 嘗試點擊按鈕，如果不可點擊則重試（最多5次，每次等待1秒）
        max_retries = 5
        for retry_count in range(max_retries):
            try:
                # 重新獲取按鈕元素
                next_button = driver.find_element(
                    By.CSS_SELECTOR,
                    ".ant-btn.css-var-r0.ant-btn-primary.pagination__PageButton-sc-1352b46e-0.hPROFu"
                )
                
                # 再次檢查是否被禁用
                if next_button.get_attribute("disabled"):
                    print("已到達最後一頁（按鈕被禁用）")
                    return False
                
                # 檢查按鈕是否可點擊
                if next_button.is_enabled() and next_button.is_displayed():
                    # 滾動到按鈕位置確保可見
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                    time.sleep(0.3)
                    
                    # 嘗試點擊
                    next_button.click()
                    print("已點擊下一頁按鈕")
                    return True
                else:
                    # 如果按鈕不可點擊，等待1秒後重試
                    if retry_count < max_retries - 1:
                        print(f"按鈕尚未可點擊，等待1秒後重試（第 {retry_count + 1}/{max_retries} 次）...")
                        time.sleep(1)
                    else:
                        print("按鈕在5秒內仍無法點擊")
                        return False
            except Exception as click_error:
                # 如果點擊失敗，等待1秒後重試
                if retry_count < max_retries - 1:
                    print(f"點擊失敗，等待1秒後重試（第 {retry_count + 1}/{max_retries} 次）...")
                    time.sleep(1)
                else:
                    print(f"點擊失敗，已達最大重試次數: {click_error}")
                    return False
        
        return False
    except Exception as e:
        # 如果等待超時，可能是最後一頁或頁面載入問題
        try:
            # 再次嘗試查找按鈕，檢查是否被禁用
            next_button = driver.find_element(
                By.CSS_SELECTOR,
                ".ant-btn.css-var-r0.ant-btn-primary.pagination__PageButton-sc-1352b46e-0.hPROFu"
            )
            if next_button.get_attribute("disabled"):
                print("已到達最後一頁（按鈕被禁用）")
                return False
        except:
            pass
        
        print(f"等待下一頁按鈕超時或發生錯誤: {e}")
        return False


def scrape_and_save_links(driver, csv_filename='link.csv'):
    """抓取當前頁面的連結並寫入 CSV，如果無法抓取則重試（最多5次）"""
    file_exists = os.path.exists(csv_filename)
    max_retries = 5
    
    # 重試機制：如果無法抓取資料，等待1秒後重試，最多5次
    for retry_count in range(max_retries):
        try:
            # 抓取當前頁面的連結
            elements = driver.find_elements(By.CSS_SELECTOR, "div.ant-col.ant-col-24.css-var-r0 a[data-sns-link]")
            sns_links = [el.get_attribute("data-sns-link") for el in elements if el.get_attribute("data-sns-link")]
            
            # 如果成功抓到連結，處理並返回
            if sns_links and len(sns_links) > 0:
                print(f"\n當前頁面抓取到 {len(sns_links)} 個連結")
                
                write_header = not file_exists  # 若檔案不存在要寫 header
                with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    if write_header:
                        writer.writerow(['link', 'image_done'])
                    for link in sns_links:
                        if link:  # 確保連結不為空
                            writer.writerow([link, ""])  # image_done 預設空字串
                print(f"已寫入 {len(sns_links)} 筆連結到 {csv_filename}")
                return len(sns_links)
            else:
                # 如果沒有抓到連結，且還有重試機會，則等待後重試
                if retry_count < max_retries - 1:
                    print(f"無法抓取到連結，等待1秒後重試（第 {retry_count + 1}/{max_retries} 次）...")
                    time.sleep(1)
                else:
                    print("無法抓取到連結，已達最大重試次數")
                    return 0
                    
        except Exception as e:
            # 如果發生錯誤，且還有重試機會，則等待後重試
            if retry_count < max_retries - 1:
                print(f"抓取連結時發生錯誤: {e}，等待1秒後重試（第 {retry_count + 1}/{max_retries} 次）...")
                time.sleep(1)
            else:
                print(f"抓取連結時發生錯誤，已達最大重試次數: {e}")
                return 0
    
    return 0


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


def take_full_page_screenshot(driver, save_path):
    """進行長截圖（全頁面截圖）"""
    try:
        # 獲取頁面總高度和寬度
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        viewport_width = driver.execute_script("return window.innerWidth")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # 設定視窗大小
        driver.set_window_size(viewport_width, viewport_height)
        
        # 如果頁面高度小於視窗高度，直接截圖
        if total_height <= viewport_height:
            driver.save_screenshot(save_path)
            return True
        
        # 需要滾動截圖並合併（最多3張）
        from PIL import Image
        import io
        
        max_screenshots = 3  # 最多合併3張截圖
        screenshots = []
        scroll_position = 0
        
        while scroll_position < total_height and len(screenshots) < max_screenshots:
            # 滾動到當前位置
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(0.8)  # 等待頁面載入和動畫完成
            
            # 截圖
            screenshot = driver.get_screenshot_as_png()
            screenshots.append(screenshot)
            
            # 更新滾動位置
            scroll_position += viewport_height
            
            # 如果已經到達底部，停止
            current_scroll = driver.execute_script("return window.pageYOffset + window.innerHeight;")
            if current_scroll >= total_height - 10:  # 10px 的容差
                break
        
        # 滾動回頂部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # 合併截圖（最多3張）
        if len(screenshots) == 1:
            with open(save_path, 'wb') as f:
                f.write(screenshots[0])
        else:
            # 只取前3張截圖
            screenshots = screenshots[:max_screenshots]
            images = [Image.open(io.BytesIO(img)) for img in screenshots]
            total_width = max(img.width for img in images)
            
            # 計算總高度（所有截圖的完整高度）
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


def screenshot_instagram_pages(csv_filename='link.csv', image_folder='image', driver=None):
    """讀取 CSV 檔案，對未完成的 Instagram 頁面進行截圖"""
    # 建立 image 資料夾
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        print(f"已建立資料夾: {image_folder}")
    
    # 讀取 CSV 檔案
    if not os.path.exists(csv_filename):
        print(f"錯誤：找不到 CSV 檔案 {csv_filename}")
        return
    
    # 初始化 driver（如果沒有提供）
    if driver is None:
        driver = setup_driver()
        close_driver = True
    else:
        close_driver = False
    
    try:
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
                
                # 檢查是否已完成
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
                    # 開啟頁面
                    print(f"正在開啟頁面...")
                    driver.get(url)
                    time.sleep(5)  # 等待頁面載入
                    
                    # 進行長截圖
                    image_path = os.path.join(image_folder, f"{username}.png")
                    print(f"正在截圖...")
                    
                    # 使用 Selenium 4 的長截圖功能
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
                    
                    # 短暫延遲，避免請求過快
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"處理 {url} 時發生錯誤: {e}")
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
        if close_driver and driver:
            driver.quit()
            print("瀏覽器已關閉")

def main():
    """主函數"""
    url = "https://app.kolr.ai/search?country_code=tw&filter_kol_type=all&follower_end_to=20000&follower_start_from=10000&gender=Female&mode=kol&platform_type=ig&sort=followerCount"
    csv_filename = 'link.csv'
    max_pages = 1000  # 安全上限，防止無限循環（通常不會達到）
    
    driver = open_page(url)
    
    if not driver:
        print("無法初始化瀏覽器")
        return
    
    try:
        page_count = 0
        total_saved = 0
        is_last_page = False
        
        # 使用無限迴圈，基於頁碼檢測來結束
        while True:
            page_count += 1
            print(f"\n{'='*50}")
            print(f"正在處理第 {page_count} 頁")
            print(f"{'='*50}")
            
            # 等待頁面內容載入
            time.sleep(2)
            
            # 獲取當前頁碼和總頁碼
            current_page, total_pages = get_page_info(driver)
            if current_page is not None and total_pages is not None:
                print(f"頁碼資訊：{current_page} / {total_pages} 頁")
                
                # 檢查是否已到達最後一頁
                if current_page >= total_pages:
                    is_last_page = True
                    print(f"已到達最後一頁（{current_page} / {total_pages}）")
            
            # 抓取並保存連結
            saved_count = scrape_and_save_links(driver, csv_filename)
            total_saved += saved_count
            
            # 如果是最後一頁，抓取完資料後結束
            if is_last_page:
                print(f"\n已到達最後一頁並完成資料抓取，結束爬取")
                break
            
            # 安全檢查：防止無限循環（如果無法獲取頁碼資訊）
            if page_count >= max_pages:
                print(f"\n達到安全上限（{max_pages} 頁），結束爬取")
                break
            
            # 嘗試點擊下一頁（會等待按鈕可點擊，確保頁面載入完畢）
            if not click_next_button(driver):
                # 如果無法點擊，再次確認是否為最後一頁
                current_page_check, total_pages_check = get_page_info(driver)
                if current_page_check is not None and total_pages_check is not None:
                    if current_page_check >= total_pages_check:
                        print(f"\n確認已到達最後一頁（{current_page_check} / {total_pages_check}），結束爬取")
                        break
                    else:
                        print(f"\n警告：無法點擊下一頁按鈕，但頁碼顯示還有更多頁（{current_page_check} / {total_pages_check}）")
                        print("等待更長時間後重試...")
                        time.sleep(5)
                        # 重試一次
                        if not click_next_button(driver):
                            print("重試失敗，結束爬取")
                            break
                else:
                    print("\n無法獲取頁碼資訊且無法點擊下一頁，結束爬取")
                    break
            
            # 等待新頁面載入完畢
            print("等待新頁面載入...")
            time.sleep(3)
            
            # 可選：顯示進度
            print(f"目前總共已保存 {total_saved} 筆連結")
        
        print(f"\n{'='*50}")
        print(f"爬蟲執行完成！")
        print(f"總共處理了 {page_count} 頁")
        print(f"總共保存了 {total_saved} 筆新連結到 {csv_filename}")
        print(f"{'='*50}")
        
    except KeyboardInterrupt:
        print("\n\n用戶中斷執行")
    except Exception as e:
        print(f"\n發生錯誤: {e}")
    finally:
        if driver:
            driver.quit()
            print("瀏覽器已關閉")

def screenshot_main():
    """截圖主函數"""
    csv_filename = 'link.csv'
    image_folder = 'image'
    
    print("開始 Instagram 頁面截圖任務...")
    screenshot_instagram_pages(csv_filename, image_folder)


if __name__ == "__main__":
    # 執行原本的爬蟲任務
    main()
    
    # 如果需要執行截圖任務，取消下面的註解
    # screenshot_main()
