import streamlit as st
import feedparser
import time
from datetime import datetime, timedelta
import json
import os

# ================= 頁面設定 =================
st.set_page_config(
    page_title="ThaiNews.Ai | 戰情室", 
    page_icon="🇹🇭", 
    layout="wide"
)

# ================= CSS 美化 (極簡卡片風) =================
st.markdown("""
<style>
    .big-font { font-size: 32px !important; font-weight: 800; color: #1a1a1a; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .stCode { border: 1px solid #d93025; }
    
    /* 新聞卡片樣式 */
    .news-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        border-left: 5px solid #d93025; /* 泰國紅 */
        transition: transform 0.2s;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .news-title {
        font-size: 18px;
        font-weight: 700;
        color: #1a1a1a;
        text-decoration: none;
        display: block;
        margin-bottom: 5px;
    }
    .news-meta {
        font-size: 14px;
        color: #666;
    }
    .news-tag {
        background-color: #f0f0f0;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-left: 10px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# ================= 爬蟲核心邏輯 =================

def get_rss_sources(days, custom_keyword=None):
    sources = []
    
    # === 模式 A：深度鑽研 (只搜自訂) ===
    if custom_keyword and custom_keyword.strip():
        clean_keyword = custom_keyword.strip().replace(" ", "+")
        sources.append({
            "name": f"🔍 深度追蹤: {custom_keyword}",
            "url": f"https://news.google.com/rss/search?q={clean_keyword}+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
        })
        return sources

    # === 模式 B：廣度掃描 (預設四大類 - 已調整順序與新增台商) ===
    
    # 定義重點台商清單 (使用 OR 語法串接)
    # 注意：使用英文名稱搜尋泰國新聞較準確，並加上引號確保精準匹配
    vip_companies = [
        '"Delta Electronics"', 
        '"Zhen Ding"', 
        '"Unimicron"', 
        '"Compeq"', 
        '"Gold Circuit Electronics"', 
        '"Dynamic Holding"', 
        '"Tripod Technology"', 
        '"Unitech"'
    ]
    # 組合搜尋字串: Thailand AND (A OR B OR C ...)
    vip_query = "+OR+".join(vip_companies)
    
    sources.extend([
        {
            "name": "🇹🇭 1. 泰國整體重要新聞", 
            "url": f"https://news.google.com/rss/search?q=Thailand+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
        },
        {
            "name": "🇹🇼 2. 台泰關係 (已調前)", 
            "url": f"https://news.google.com/rss/search?q=Thailand+Taiwan+OR+%22Taiwanese+investment%22+OR+%22Taiwan+companies%22+OR+%22Trade+Relations%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
        },
        {
            "name": "🔌 3. PCB 與電子製造", 
            "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+%22Printed+Circuit+Board%22+OR+%22Electronics+Manufacturing%22+OR+%22Server+Production%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
        },
        {
            "name": "🏢 4. 重點台商動態追蹤