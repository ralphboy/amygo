import streamlit as st
import feedparser
import time
from datetime import datetime
import json
import os

# ================= 1. 頁面設定 (必須放第一行) =================
st.set_page_config(
    page_title="ThaiNews.Ai | 戰情室", 
    page_icon="🇹🇭", 
    layout="wide"
)

# ================= 2. 常數與 CSS 設定 =================

# CSS 美化樣式
CUSTOM_CSS = """
<style>
    .big-font { font-size: 28px !important; font-weight: 800; color: #1a1a1a; margin-bottom: 20px !important; }
    
    /* 緊湊化調整 */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }
    
    .news-card {
        background-color: white;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 8px;
        border-left: 4px solid #d93025;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .news-title {
        font-size: 16px;
        font-weight: 700;
        color: #1a1a1a;
        text-decoration: none;
        display: block;
        margin-bottom: 4px;
    }
    .news-meta { font-size: 13px; color: #666; }
    .news-tag {
        background-color: #f0f0f0;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        margin-left: 8px;
        color: #555;
    }
    
    /* 隱藏預設連結符號 */
    .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a, .stMarkdown h4 a, .stMarkdown h5 a {
        display: none !important;
    }
    
    /* 手機版適配 */
    @media (max-width: 768px) {
        .mobile-hidden { display: none !important; }
        .block-container { padding-top: 2rem !important; }
    }
</style>
"""

# VIP 公司清單
VIP_COMPANIES_EN = [
    '"Delta Electronics"', '"Zhen Ding"', '"Unimicron"', '"Compeq"', 
    '"Gold Circuit Electronics"', '"Dynamic Holding"', '"Tripod Technology"', 
    '"Unitech"', '"Foxconn"', '"Inventec"'
]

VIP_COMPANIES_CN = [
    '"台達電"', '"臻鼎"', '"欣興"', '"華通"', 
    '"金像電"', '"定穎"', '"健鼎"', 
    '"燿華"', '"鴻海"', '"英業達"'
]

# 預先計算好查詢字串 (避免在函式內重複計算)
VIP_QUERY_EN = "+OR+".join([c.replace(" ", "+") for c in VIP_COMPANIES_EN])
VIP_QUERY_CN = "+OR+".join([c.replace(" ", "+") for c in VIP_COMPANIES_CN])

# 選項映射
DATE_MAP = {
    "1天": 1, "3天": 3, "1週": 7, "2週": 14,
    "1月": 30, "3月": 90, "6月": 180
}

TOPIC_MAP = {
    "泰國政經": "macro",
    "電子產業": "industry",
    "重點台商": "vip"
}

# 套用 CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ================= 3. 爬蟲核心邏輯 =================

def get_rss_sources(days, mode="all", custom_keyword=None):
    """
    產生 RSS 來源列表
    :param days: 天數 (int) -> 這裡就是 traceback 報錯的地方，必須確保參數名為 days
    """
    sources = []
    
    # 自訂搜尋模式
    if mode == "custom" and custom_keyword:
        clean_keyword = custom_keyword.strip().replace(" ", "+")
        sources.append({
            "name": f"🔍 深度追蹤: {custom_keyword} (中)",
            "url": f"https://news.google.com/rss/search?q={clean_keyword}+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        })
        sources.append({
            "name": f"🔍 深度追蹤: {custom_keyword} (EN)",
            "url": f"https://news.google.com/rss/search?q={clean_keyword}+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
        })
        return sources

    # 預設模式
    if mode == "macro":
        sources.extend([
            {"name": "🇹🇭 泰國整體 (中)", "url": f"https://news.google.com/rss/search?q=泰國+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🇹🇭 泰國整體 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"},
            {"name": "🇹🇼 台泰關係 (中)", "url": f"https://news.google.com/rss/search?q=泰國+台灣+OR+%22台商%22+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🇹🇼 台泰關係 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+Taiwan+OR+%22Taiwanese+investment%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"}
        ])
    elif mode == "industry":
        sources.extend([
            {"name": "🔌 PCB製造 (中)", "url": f"https://news.google.com/rss/search?q=泰國+PCB+OR+%22電子製造%22+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🔌 PCB製造 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+%22Electronics+Manufacturing%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"}
        ])
    elif mode == "vip":
        # 使用全域變數 VIP_QUERY_CN/EN
        sources.extend([
            {"name": "🏢 台商動態 (中)", "url": f"https://news.google.com/rss/search?q=泰國+OR+{VIP_QUERY_CN}+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🏢 台商動態 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+{VIP_QUERY_EN}+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"}
        ])
    
    return sources

def generate_chatgpt_prompt(days_label, days_int, search_mode, custom_keyword=None):
    status_text = st.empty() 
    progress_bar = st.progress(0)
    
    # 呼叫 get_rss_sources，並傳入 days_int 作為 days 參數
    sources = get_rss_sources(days_int, search_mode, custom_keyword)
    news_items_for_json = []

    if search_mode == "custom":
        instruction_prompt = f"針對關鍵字【{custom_keyword}】，請撰寫一份深度分析報告：1. 重點摘要 2. 市場影響 3. 機會與風險。"
    elif search_mode == "macro":
        instruction_prompt = f"請分析【{days_label} 泰國整體與台泰關係】：1. 泰國政經局勢 2. 台泰雙邊互動。"
    elif search_mode == "industry":
        instruction_prompt = f"請分析【{days_label} 泰國 PCB 與電子製造】：1. 產業趨勢 2. 供應鏈動態。"
    elif search_mode == "vip":
        instruction_prompt = f"請分析【{days_label} 泰國重點台商】：1. 個股動態 2. 投資訊號。"

    output_text = f"""
請扮演一位資深的「產業分析師」。
{instruction_prompt}
請用**繁體中文**，並以 **Markdown** 條列式輸出，風格需專業且易讀。

========= 以下是新聞資料庫 ({datetime.now().strftime('%Y-%m-%d')}) =========
"""
    
    seen_titles = set()
    total_steps = len(sources)
    
    for i, source in enumerate(sources):
        status_text.text(f"📡 掃描: {source['name']} ...")
        
        try:
            feed = feedparser.parse(source['url'])
            if len(feed.entries) > 0:
                output_text += f"\n## 【{source['name']}】\n"
                
                # 自訂搜尋不設限，預設限制 30 篇
                limit = len(feed.entries) if search_mode == "custom" else 30
                
                for entry in feed.entries[:limit]: 
                    if entry.title in seen_titles: continue
                    seen_titles.add(entry.title)
                    source_name = entry.source.title if 'source' in entry else "Google News"
                    pub_date = entry.published if 'published' in entry else ""
                    output_text += f"- [{pub_date}] [{source_name}] {entry.title}\n  連結: {entry.link}\n"
                    news_items_for_json.append({
                        "title": entry.title, "link": entry.link, "date": pub_date,
                        "source": source_name, "category": source['name']
                    })
            else:
                output_text += f"\n## 【{source['name']}】\n(無相關新聞)\n"
        except Exception as e:
            st.error(f"錯誤: {e}")
        
        progress_bar.progress((i + 1) / total_steps)
        time.sleep(0.3)

    output_text += "\n========= 資料結束 ========="
    
    try:
        with open('news_data.json', 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "news_list": news_items_for_json
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"存檔失敗: {e}")

    status_text.text("✅ 完成！")
    time.sleep(0.5)
    status_text.empty()
    progress_bar.empty()
    
    return output_text, news_items_for_json

def display_results(prompt, news_list):
    """顯示搜尋結果的共用函數"""
    st.markdown("##### 1. AI 分析指令")
    with st.expander("點擊展開查看 Prompt", expanded=False):
        st.code(prompt, language="markdown")
        
    st.markdown("##### 2. 相關新聞速覽")
    if news_list:
        for news in news_list:
            cat = news.get('category', '一般')
            st.markdown(f'''
            <div class="news-card">
                <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                <div class="news-meta">{news['date']} • {news['source']} <span class="news-tag">{cat}</span></div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.warning("查無新聞資料。")

# ================= 4. 網頁主程式 =================

st.markdown('<div class="big-font">ThaiNews.Ai 🇹🇭 戰情室</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🤖 生成器", "📊 歷史庫"])

with tab1:
    # 核心版面：左控右顯
    c_left, c_right = st.columns([1, 3], gap="medium")
    
    with c_left:
        st.markdown('<h5 class="mobile-hidden">⚙️ 設定操作</h5>', unsafe_allow_html=True)
        
        # [狀態管理]
        if 'days_int' not in st.session_state: st.session_state['days_int'] = 1 
        if 'search_type' not in st.session_state: st.session_state['search_type'] = None
        if 'search_keyword' not in st.session_state: st.session_state['search_keyword'] = ""
        if 'last_topic' not in st.session_state: st.session_state['last_topic'] = None
        
        # [Helper] 設定搜尋模式
        def set_search(mode, keyword=""):
            st.session_state['search_type'] = mode
            st.session_state['search_keyword'] = keyword

        # 1. 時間選擇
        st.caption("1. 時間範圍")
        # 注意: st.pills 需要 Streamlit 1.40.0+
        try:
            date_selection = st.pills("Time", list(DATE_MAP.keys()), default="1天", label_visibility="collapsed", key="pills_date")
        except AttributeError:
            st.error("請更新 Streamlit 版本至 1.40+ 以使用 Pills 元件，或改用 Radio。")
            date_selection = st.radio("Time", list(DATE_MAP.keys()), horizontal=True, label_visibility="collapsed")
            
        if date_selection:
            st.session_state['days_int'] = DATE_MAP[date_selection] 

        # 2. 主題選擇
        st.caption("2. 分析主題")
        try:
            topic_selection = st.pills("Topic", list(TOPIC_MAP.keys()), label_visibility="collapsed", selection_mode="single", key="pills_topic")
        except AttributeError:
            topic_selection = st.radio("Topic", ["(請選擇)"] + list(TOPIC_MAP.keys()), label_visibility="collapsed")
            if topic_selection == "(請選擇)": topic_selection = None
        
        if topic_selection:
            target_mode = TOPIC_MAP[topic_selection]
            if st.session_state.get('last_topic') != topic_selection:
                st.session_state['last_topic'] = topic_selection 
                set_search(target_mode)
                st.rerun() 
        
        # 3. 自訂搜尋
        st.caption("3. 關鍵字")
        def handle_custom_search():
            kw = st.session_state.kw_input
            if kw:
                # 清除主題選取 (如果使用 pills)
                try:
                    st.session_state['pills_topic'] = None 
                except:
                    pass
                st.session_state['last_topic'] = None
                set_search("custom", kw)

        c_in, c_btn = st.columns([3, 1], gap="small")
        with c_in:
            st.text_input("Keywords", placeholder="輸入關鍵字", key="kw_input", on_change=handle_custom_search, label_visibility="collapsed")
        with c_btn:
            st.button("🔍", type="primary", use_container_width=True, on_click=handle_custom_search)

    # 右側：顯示結果區域
    with c_right:
        days_int = st.session_state['days_int']
        selected_label = next((k for k, v in DATE_MAP.items() if v == days_int), f"{days_int}天")
        
        s_type = st.session_state.get('search_type')
        s_kw = st.session_state.get('search_keyword')

        # 尚未搜尋時的歡迎畫面
        if not s_type:
            st.info("👈 請從左側選擇主題或輸入關鍵字開始。")
            st.markdown("""
            <div style="background:#f8f9fa; padding:15px; border-radius:10px; color:#555;">
                <strong>💡 系統說明：</strong><br>
                1. <b>泰國政經</b>：政經局勢與台泰關係。<br>
                2. <b>電子產業</b>：PCB、伺服器與電子製造。<br>
                3. <b>重點台商</b>：鎖定 10 大指標台廠動態。
            </div>
            """, unsafe_allow_html=True)
        
        # 執行搜尋
        else:
            if s_type == "custom" and s_kw:
                with st.spinner(f"正在全網搜索 {s_kw}..."):
                    prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "custom", s_kw)
                    display_results(prompt, news_list)
                    
            elif s_type == "macro":
                with st.spinner("正在掃描泰國大選、經貿與台泰新聞..."):
                    prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "macro")
                    display_results(prompt, news_list)
                    
            elif s_type == "industry":
                with st.spinner("正在掃描 PCB 與電子供應鏈新聞..."):
                    prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "industry")
                    display_results(prompt, news_list)
                    
            elif s_type == "vip":
                with st.spinner("正在掃描重點台商動態..."):
                    prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "vip")
                    display_results(prompt, news_list)

with tab2:
    col_head_1, col_head_2 = st.columns([3, 1])
    with col_head_1:
        st.markdown("### 📂 歷史新聞資料庫")
    with col_head_2:
        if st.button("🔄 刷新列表"): st.rerun()
    
    if os.path.exists('news_data.json'):
        with open('news_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        news_list = data.get('news_list', [])
        st.caption(f"📅 上次更新: {data.get('timestamp', '未知')} (共 {len(news_list)} 則)")

        search_query = st.text_input("🔍 搜尋歷史...", placeholder="請輸入標題關鍵字")
        if search_query:
            news_list = [n for n in news_list if search_query.lower() in n['title'].lower()]

        if news_list:
            for news in news_list:
                cat = news.get('category', '歷史')
                st.markdown(f"""
                <div class="news-card">
                    <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                    <div class="news-meta">{news['date']} • {news['source']} <span class="news-tag">{cat}</span></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("無符合資料")
    else:
        st.info("尚無歷史紀錄，請先在生成器執行搜尋。")