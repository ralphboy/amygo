import streamlit as st
import feedparser
import time
from datetime import datetime
import json
import os
import concurrent.futures
import html
import urllib.parse
from typing import List, Dict, Tuple, Optional, Any

# ================= 1. Constants =================

# VIP 公司清單 (印尼重點台商)
# Includes user-added ASUS and Acer
VIP_COMPANIES_EN: List[str] = [
    '"Foxconn"', '"Hon Hai"', '"Pegatron"', '"Delta Electronics"', 
    '"Compal"', '"Gogoro"', '"Kymco"', '"Pou Chen"', 
    '"Eclat Textile"', '"Cheng Shin"', '"CTBC Bank"',
    '"ASUS"', '"Acer"'
]

VIP_COMPANIES_CN: List[str] = [
    '鴻海', '富士康', '和碩', '台達電', 
    '仁寶', 'Gogoro', '光陽', '寶成', 
    '儒鴻', '正新', '中信銀',
    '華碩', '宏碁'
]

# 預先計算好查詢字串
# Google News RSS strictness check: Use %20 for spaces
# Use logic from verified fix: quote() and %20OR%20
# Also user's version had wrapping parentheses, which is good for boolean logic security.
VIP_QUERY_EN: str = "(" + "%20OR%20".join([urllib.parse.quote(c) for c in VIP_COMPANIES_EN]) + ")"
VIP_QUERY_CN: str = "(" + "%20OR%20".join([urllib.parse.quote(c) for c in VIP_COMPANIES_CN]) + ")"

# 選項映射
DATE_MAP: Dict[str, int] = {
    "3天": 3, "1週": 7, "1月": 30
}

TOPIC_MAP: Dict[str, str] = {
    "印尼政經": "macro",
    "電動車與供應鏈": "industry",
    "重點台商": "vip"
}

# ================= 2. Helper Functions =================

def get_rss_sources(days: int, mode: str = "all", custom_keyword: Optional[str] = None) -> List[Dict[str, str]]:
    """
    產生 RSS 來源列表
    :param days: 天數 (int)
    :param mode: 搜尋模式 (custom, macro, industry, vip)
    :param custom_keyword: 自訂關鍵字
    """
    sources = []
    
    # 自訂搜尋模式
    if mode == "custom" and custom_keyword:
        # Improved URL encoding: use quote() for %20
        clean_keyword = custom_keyword.strip()
        encoded_keyword = urllib.parse.quote(clean_keyword)
        
        sources.append({
            "name": f"🔍 深度追蹤: {clean_keyword} (中)",
            "url": f"https://news.google.com/rss/search?q={encoded_keyword}%20when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        })
        sources.append({
            "name": f"🔍 深度追蹤: {clean_keyword} (EN)",
            "url": f"https://news.google.com/rss/search?q={encoded_keyword}%20when:{days}d&hl=en-ID&gl=ID&ceid=ID:en"
        })
        return sources

    # 預設模式
    if mode == "macro":
        sources.extend([
            {"name": "🇮🇩 印尼整體 (中)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('印尼')}%20when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🇮🇩 印尼整體 (EN)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('Indonesia')}%20when:{days}d&hl=en-ID&gl=ID&ceid=ID:en"},
            {"name": "🇹🇼 台印關係 (中)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('印尼 台灣 OR "台商"')}%20when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🇹🇼 台印關係 (EN)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('Indonesia Taiwan OR "Taiwanese investment"')}%20when:{days}d&hl=en-ID&gl=ID&ceid=ID:en"}
        ])
    elif mode == "industry":
        # 印尼關鍵字：EV, Battery, Nickel, Electronics
        sources.extend([
            {"name": "⚡ EV/電子 (中)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('印尼 電動車 OR 電池 OR "電子製造"')}%20when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "⚡ EV/Electronics (EN)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('Indonesia EV OR Battery OR Nickel OR Electronics Manufacturing')}%20when:{days}d&hl=en-ID&gl=ID&ceid=ID:en"}
        ])
    elif mode == "vip":
        # 使用全域變數 VIP_QUERY_CN/EN
        # 注意: 這裡的 URL 已經由 VIP_QUERY_* 處理好編碼的一部分 (%20OR%20)
        # Optimized logic: (Indonesia) AND (Company A OR Company B...)
        sources.extend([
            {"name": "🏢 台商動態 (中)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('印尼')}%20{VIP_QUERY_CN}%20when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🏢 台商動態 (EN)", "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('Indonesia')}%20{VIP_QUERY_EN}%20when:{days}d&hl=en-ID&gl=ID&ceid=ID:en"}
        ])
    
    return sources

def fetch_feed(source: Dict[str, str]) -> Tuple[Dict[str, str], Any]:
    """Helper function to fetch a single RSS feed."""
    try:
        # Best practice: Add User-Agent headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Note: feedparser allows passing headers or agent, but it's often better to fetch content with requests first
        # However, to keep it simple and consistent with previous working version, let's use feedparser's built-in http support first.
        # If google blocks it, we might need requests. But debug script showed logic.fetch_feed working with valid URL.
        # Let's keep it simple as in Step 22/115 but with correct URLs.
        return source, feedparser.parse(source['url'])
    except Exception as e:
        return source, None

def generate_chatgpt_prompt(days_label: str, days_int: int, search_mode: str, custom_keyword: Optional[str] = None) -> Tuple[str, List[Dict[str, str]]]:
    """
    執行爬蟲並生成 Prompt
    """
    status_text = st.empty() 
    progress_bar = st.progress(0)
    
    # 呼叫 get_rss_sources，並傳入 days_int 作為 days 參數
    sources = get_rss_sources(days_int, search_mode, custom_keyword)
    news_items_for_json = []

    if search_mode == "custom":
        instruction_prompt = f"針對關鍵字【{custom_keyword}】，請撰寫一份深度分析報告：1. 重點摘要 2. 市場影響 3. 機會與風險。"
    elif search_mode == "macro":
        instruction_prompt = f"請分析【{days_label} 印尼整體與台印關係】：1. 印尼政經局勢 (含新首都/政策) 2. 台印雙邊互動。"
    elif search_mode == "industry":
        instruction_prompt = f"請分析【{days_label} 印尼電動車與電子產業】：1. 產業趨勢 (EV/電池/鎳礦) 2. 供應鏈動態。"
    elif search_mode == "vip":
        instruction_prompt = f"請分析【{days_label} 印尼重點台商】：1. 個股動態 2. 投資訊號。"
    else:
        instruction_prompt = "請分析以下新聞。"

    output_text = f"""
請扮演一位資深的「東南亞產業分析師」。
{instruction_prompt}
請用**繁體中文**，並以 **Markdown** 條列式輸出，風格需專業且易讀。

========= 以下是新聞資料庫 ({datetime.now().strftime('%Y-%m-%d')}) =========
"""
    
    seen_titles = set()
    total_steps = len(sources)
    
    # 平行抓取 RSS
    status_text.text(f"📡 正在平行掃描 {len(sources)} 個來源...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {executor.submit(fetch_feed, source): source for source in sources}
        
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_source):
            completed_count += 1
            progress_bar.progress(completed_count / total_steps)
            
            source, feed = future.result()
            
            if feed and len(feed.entries) > 0:
                output_text += f"\\n## 【{source['name']}】\\n"
                
                # 自訂搜尋不設限，預設限制 30 篇
                limit = len(feed.entries) if search_mode == "custom" else 30
                
                for entry in feed.entries[:limit]: 
                    if entry.title in seen_titles: continue
                    seen_titles.add(entry.title)
                    source_name = entry.source.title if 'source' in entry else "Google News"
                    pub_date = entry.published if 'published' in entry else ""
                    link = entry.link
                    
                    output_text += f"- [{pub_date}] [{source_name}] {entry.title}\\n  連結: {link}\\n"
                    news_items_for_json.append({
                        "title": entry.title, "link": link, "date": pub_date,
                        "source": source_name, "category": source['name']
                    })
            else:
                output_text += f"\\n## 【{source['name']}】\\n(無相關新聞)\\n"

    output_text += "\\n========= 資料結束 ========="
    
    # 累積歷史資料邏輯
    try:
        existing_data = {"news_list": []}
        if os.path.exists('news_data.json'):
            with open('news_data.json', 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    pass # 檔案損毀則使用空列表
        
        # 建立現有連結集合以過濾重複
        existing_list = existing_data.get('news_list', [])
        existing_links = set(item['link'] for item in existing_list)
        
        # Insert new items
        for item in news_items_for_json:
            if item['link'] not in existing_links:
                existing_list.insert(0, item) # 新的放前面
                existing_links.add(item['link'])
        
        # Optimization: Limit to latest 1000 items
        if len(existing_list) > 1000:
            existing_list = existing_list[:1000]
        
        existing_data['news_list'] = existing_list
        existing_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open('news_data.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"存檔失敗: {e}")

    status_text.text("✅ 完成！")
    time.sleep(0.5)
    status_text.empty()
    progress_bar.empty()
    
    return output_text, news_items_for_json