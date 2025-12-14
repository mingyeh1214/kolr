"""
KOLR.ai 爬蟲腳本 (手動登入模式)
先進入搜尋頁面，等待用戶手動登入，然後停留在頁面等待進一步指示
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import json
import time
import sys
import io
from typing import List, Dict, Optional
import csv

# 設置 UTF-8 編碼以支持 Windows 終端
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class KOLRManualLoginScraper:
    def __init__(self, headless: bool = False):
        """
        初始化 Selenium 爬蟲（手動登入模式）
        
        Args:
            headless: 是否使用無頭模式（不顯示瀏覽器視窗）
        """
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = None
        self.base_url = "https://app.kolr.ai"
    
    def start_driver(self):
        """啟動瀏覽器驅動"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.maximize_window()
            print("[OK] 瀏覽器已啟動")
        except Exception as e:
            print(f"[ERROR] 啟動瀏覽器失敗: {e}")
            print("請確保已安裝 ChromeDriver 並在 PATH 中")
            raise
    
    def close_driver(self):
        """關閉瀏覽器驅動"""
        if self.driver:
            self.driver.quit()
            print("瀏覽器已關閉")
    
    def wait_for_manual_login(self, url: str, wait_seconds: int = 30):
        """
        進入搜尋頁面並等待用戶手動登入
        
        Args:
            url: 目標搜尋頁面 URL
            wait_seconds: 等待時間（秒）
        """
        if not self.driver:
            self.start_driver()
        
        try:
            print(f"\n正在訪問搜尋頁面...")
            print(f"URL: {url}")
            self.driver.get(url)
            
            # 等待頁面載入
            time.sleep(3)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            print(f"\n當前頁面標題: {page_title}")
            print(f"當前 URL: {current_url}")
            
            # 檢查是否被重定向到登入頁面
            if 'login' in current_url.lower() or '登入' in page_title:
                print("\n[WARNING] 檢測到登入頁面")
                print(f"請在瀏覽器中手動完成登入...")
                print(f"等待 {wait_seconds} 秒...")
                
                # 倒數計時
                for i in range(wait_seconds, 0, -1):
                    print(f"剩餘時間: {i} 秒", end='\r')
                    time.sleep(1)
                print("\n")
            else:
                print("\n[OK] 似乎已經在搜尋頁面，等待載入...")
                time.sleep(5)
            
            # 再次檢查當前狀態
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            print(f"\n=== 當前狀態 ===")
            print(f"頁面標題: {page_title}")
            print(f"當前 URL: {current_url}")
            
            if 'login' in current_url.lower() or '登入' in page_title:
                print("\n[WARNING] 仍在登入頁面")
                print("如果已經登入，請手動導航到搜尋頁面")
            else:
                print("\n[OK] 已進入搜尋頁面")
            
            print(f"\n{'='*60}")
            print("瀏覽器將保持開啟狀態")
            print("請在瀏覽器中完成登入並確保在搜尋頁面")
            print("完成後，請告訴我要爬取哪些數據")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'current_url': current_url,
                'page_title': page_title,
                'driver': self.driver
            }
            
        except Exception as e:
            print(f"[ERROR] 發生錯誤: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def wait_for_instructions(self):
        """
        保持瀏覽器開啟，等待用戶指示
        """
        print("\n" + "="*60)
        print("[OK] 瀏覽器已準備就緒")
        print("="*60)
        print("\n瀏覽器將保持開啟，等待您的進一步指示...")
        print("\n您可以告訴我要爬取哪些數據，例如：")
        print("  - 爬取所有 KOL 卡片信息")
        print("  - 爬取 KOL 名稱、粉絲數、連結等")
        print("  - 爬取特定字段的數據")
        print("\n請確保您已經：")
        print("  1. 完成登入")
        print("  2. 在搜尋結果頁面")
        print("  3. 頁面已完全載入")
        print("\n" + "="*60)
        print("腳本將保持運行，請告訴我要爬取什麼數據")
        print("="*60 + "\n")
        
        # 保持瀏覽器開啟，但不阻塞
        # 用戶可以在終端繼續輸入指令
        try:
            while True:
                time.sleep(5)  # 每5秒檢查一次
                # 檢查瀏覽器是否還在運行
                try:
                    current_url = self.driver.current_url
                    # 可以選擇性地顯示狀態
                except:
                    print("\n[WARNING] 瀏覽器已關閉")
                    break
        except KeyboardInterrupt:
            print("\n\n收到中斷信號，準備關閉瀏覽器...")
    
    def scrape_current_page(self) -> Optional[Dict]:
        """
        爬取當前頁面的數據
        """
        if not self.driver:
            print("[ERROR] 瀏覽器未啟動")
            return None
        
        try:
            print("\n開始爬取當前頁面數據...")
            
            # 等待頁面完全載入
            time.sleep(3)
            
            # 獲取頁面源代碼
            page_source = self.driver.page_source
            current_url = self.driver.current_url
            
            # 嘗試執行 JavaScript 來獲取數據
            page_info = self.driver.execute_script("""
            return {
                pageTitle: document.title,
                url: window.location.href,
                readyState: document.readyState,
                scrollHeight: document.documentElement.scrollHeight,
                scrollTop: window.pageYOffset
            };
            """)
            
            # 嘗試尋找包含 KOL 數據的元素
            selectors = [
                "[class*='kol']",
                "[class*='card']",
                "[class*='item']",
                "[class*='profile']",
                "[class*='user']",
                "[data-testid*='kol']",
                "[data-testid*='card']",
                "article",
                "[role='article']",
            ]
            
            kol_elements = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    kol_elements.extend(elements)
                except:
                    continue
            
            # 提取數據
            seen_texts = set()
            kol_data = []
            
            for element in kol_elements[:500]:  # 增加數量限制
                try:
                    text = element.text.strip()
                    if text and len(text) > 10 and text not in seen_texts:
                        seen_texts.add(text)
                        
                        item_data = {
                            'text': text,
                            'tag': element.tag_name
                        }
                        
                        # 嘗試獲取連結
                        try:
                            link_elem = element.find_element(By.TAG_NAME, "a")
                            item_data['link'] = link_elem.get_attribute('href')
                        except:
                            pass
                        
                        # 嘗試獲取圖片
                        try:
                            img_elem = element.find_element(By.TAG_NAME, "img")
                            item_data['image'] = img_elem.get_attribute('src')
                            item_data['image_alt'] = img_elem.get_attribute('alt')
                        except:
                            pass
                        
                        # 嘗試獲取所有屬性
                        try:
                            attrs = {}
                            for attr in ['class', 'id', 'data-testid', 'data-id']:
                                value = element.get_attribute(attr)
                                if value:
                                    attrs[attr] = value
                            if attrs:
                                item_data['attributes'] = attrs
                        except:
                            pass
                        
                        kol_data.append(item_data)
                except:
                    continue
            
            # 從頁面源中提取 JSON 數據
            soup = BeautifulSoup(page_source, 'html.parser')
            scripts = soup.find_all('script', type='application/json')
            json_data = []
            
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    json_data.append(data)
                except:
                    pass
            
            result = {
                'page_info': page_info,
                'kol_elements_count': len(kol_elements),
                'extracted_kol_data': kol_data,
                'json_data': json_data,
                'url': current_url,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"[OK] 找到 {len(kol_elements)} 個 KOL 相關元素")
            print(f"[OK] 提取了 {len(kol_data)} 筆數據")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 爬取錯誤: {e}")
            return None
    
    def save_to_json(self, data: Dict, filename: str = 'kolr_scraped_data.json'):
        """將數據保存為 JSON 文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] 數據已保存到 {filename}")
        except Exception as e:
            print(f"[ERROR] 保存 JSON 錯誤: {e}")
    
    def save_to_csv(self, data: List[Dict], filename: str = 'kolr_scraped_data.csv'):
        """將數據保存為 CSV 文件"""
        if not data:
            print("沒有數據可保存")
            return
        
        try:
            all_keys = set()
            for item in data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                for item in data:
                    if isinstance(item, dict):
                        # 處理嵌套的字典
                        row = {}
                        for key, value in item.items():
                            if isinstance(value, dict):
                                row[key] = json.dumps(value, ensure_ascii=False)
                            elif isinstance(value, list):
                                row[key] = json.dumps(value, ensure_ascii=False)
                            else:
                                row[key] = value
                        writer.writerow(row)
            print(f"[OK] 數據已保存到 {filename}")
        except Exception as e:
            print(f"[ERROR] 保存 CSV 錯誤: {e}")


def main():
    """主函數"""
    url = "https://app.kolr.ai/search?country_code=tw&filter_kol_type=all&follower_end_to=20000&follower_start_from=10000&gender=Female&mode=kol&platform_type=ig&sort=followerCount"
    
    scraper = KOLRManualLoginScraper(headless=False)
    
    try:
        # 進入搜尋頁面並等待手動登入
        result = scraper.wait_for_manual_login(url, wait_seconds=30)
        
        if result.get('success'):
            # 保持瀏覽器開啟，等待用戶指示
            scraper.wait_for_instructions()
        else:
            print("[ERROR] 初始化失敗")
            
    except KeyboardInterrupt:
        print("\n\n收到中斷信號...")
    except Exception as e:
        print(f"\n[ERROR] 發生錯誤: {e}")
    finally:
        print("\n準備關閉瀏覽器...")
        scraper.close_driver()


if __name__ == "__main__":
    main()

