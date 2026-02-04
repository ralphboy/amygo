# ================= 1. Constants (已更新名單) =================

# VIP 公司清單 - 新增 ASUS, Acer
VIP_COMPANIES_EN: List[str] = [
    '"Foxconn"', '"Hon Hai"', '"Pegatron"', '"Delta Electronics"', 
    '"Compal"', '"Gogoro"', '"Kymco"', '"Pou Chen"', 
    '"Eclat Textile"', '"Cheng Shin"', '"CTBC Bank"',
    '"ASUS"', '"Acer"'  # 新增
]

VIP_COMPANIES_CN: List[str] = [
    '"鴻海"', '"富士康"', '"和碩"', '"台達電"', 
    '"仁寶"', '"Gogoro"', '"光陽"', '"寶成"', 
    '"儒鴻"', '"正新"', '"中信銀"',
    '"華碩"', '"宏碁"'  # 新增
]

# 重新定義查詢字串：確保公司之間是 OR 關係
VIP_QUERY_EN: str = "(" + "%20OR%20".join([urllib.parse.quote(c) for c in VIP_COMPANIES_EN]) + ")"
VIP_QUERY_CN: str = "(" + "%20OR%20".join([urllib.parse.quote(c) for c in VIP_COMPANIES_CN]) + ")"

# ... (其餘 DATE_MAP 與 TOPIC_MAP 不變)

# ================= 2. Helper Functions (優化搜尋邏輯) =================

def get_rss_sources(days: int, mode: str = "all", custom_keyword: Optional[str] = None) -> List[Dict[str, str]]:
    sources = []
    
    # ... (custom, macro, industry 模式保持原樣)

    elif mode == "vip":
        # 優化點：將原本的 "印尼 OR" 改為 "印尼" (預設即為 AND)
        # 這樣會搜尋：(印尼) AND (公司 A OR 公司 B OR ...)
        sources.extend([
            {
                "name": "🏢 台商動態 (中)", 
                "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('印尼')}%20{VIP_QUERY_CN}%20when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            },
            {
                "name": "🏢 台商動態 (EN)", 
                "url": f"https://news.google.com/rss/search?q={urllib.parse.quote('Indonesia')}%20{VIP_QUERY_EN}%20when:{days}d&hl=en-ID&gl=ID&ceid=ID:en"
            }
        ])
    
    return sources