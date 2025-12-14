# KOLR.ai 爬蟲樣板

這是一個簡單的 Python 爬蟲樣板，用於爬取 KOLR.ai 網站的內容。

## 安裝步驟

1. 安裝 Python 依賴套件：
```bash
pip install -r requirements.txt
```

2. 確保已安裝 Chrome 瀏覽器

3. 如果使用 ChromeDriver，請確保版本與 Chrome 瀏覽器匹配，或使用 webdriver-manager 自動管理

## 使用方法

執行爬蟲腳本：
```bash
python crawler.py
```

## 注意事項

- 請遵守網站的服務條款和使用規範
- 建議在請求之間添加適當的延遲，避免對伺服器造成過大負擔
- 如果網站有反爬蟲機制，可能需要調整策略
