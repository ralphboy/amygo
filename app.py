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

# ================= CSS 美化 (左側導航版) =================
st.markdown("""
<style>
    .big-font { font-size: 28px !important; font-weight: 800; color: #1a1a1a; margin-bottom: 20px !important; }
    
    /* 緊湊化調整 */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important; /* 全局縮小垂直間距 */
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
    
    /* 隱藏標題旁的連結符號 (Anchor Link) */
    .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a, .stMarkdown h4 a, .stMarkdown h5 a {
        display: none !important;
    }
    
    /* 縮小成功訊息 (st.success) 的高度 */
    .stAlert {
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= 爬蟲核心邏輯 =================

def get_rss_sources(days, mode="all", custom_keyword=None):
    sources = []
    
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

    vip_companies_en = [
        '"Delta Electronics"', '"Zhen Ding"', '"Unimicron"', '"Compeq"', 
        '"Gold Circuit Electronics"', '"Dynamic Holding"', '"Tripod Technology"', 
        '"Unitech"', '"Foxconn"', '"Inventec"'
    ]
    vip_query_en = "+OR+".join([c.replace(" ", "+") for c in vip_companies_en])

    vip_companies_cn = [
        '"台達電"', '"臻鼎"', '"欣興"', '"華通"', 
        '"金像電"', '"定穎"', '"健鼎"', 
        '"燿華"', '"鴻海"', '"英業達"'
    ]
    vip_query_cn = "+OR+".join([c.replace(" ", "+") for c in vip_companies_cn])
    
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
        sources.extend([
            {"name": "🏢 台商動態 (中)", "url": f"https://news.google.com/rss/search?q=泰國+OR+{vip_query_cn}+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🏢 台商動態 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+{vip_query_en}+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"}
        ])
    
    return sources

def generate_chatgpt_prompt(days_label, days_int, search_mode, custom_keyword=None):
    status_text = st.empty() 
    progress_bar = st.progress(0)
    
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
                
                # 若是自訂搜尋則不設限 (抓取所有回傳結果)，否則限制 30 篇以免 Prompt 太長
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
    """顯示搜尋結果的共用函數：分為 AI 指令區 與 新聞列表區"""
    
    st.success("搜尋完成！")
    
    # 區塊 1: AI Prompt
    st.markdown("##### 1. AI 分析指令")
    with st.expander("點擊展開", expanded=False):
        st.code(prompt, language="markdown")
        
    # 區塊 2: 新聞卡片
    st.markdown("##### 2. 相關新聞速覽")
    if news_list:
        for news in news_list:
            cat = news.get('category', '一般')
            # 使用與 Tab 2 相同的卡片樣式
            st.markdown(f'''
            <div class="news-card">
                <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                <div class="news-meta">{news['date']} • {news['source']} <span class="news-tag">{cat}</span></div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.warning("查無新聞資料。")

# ================= 網頁主程式 =================

st.markdown('<div class="big-font">ThaiNews.Ai 🇹🇭 戰情室</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🤖 生成器", "📊 歷史庫"])

with tab1:
    # [狀態管理] 初始化
    if 'days_int' not in st.session_state: st.session_state['days_int'] = 1 
    if 'search_type' not in st.session_state: st.session_state['search_type'] = None
    if 'search_keyword' not in st.session_state: st.session_state['search_keyword'] = ""
    if 'settings_expanded' not in st.session_state: st.session_state['settings_expanded'] = True

    # [Callback] 設定搜尋模式並收合選單
    def set_search(mode, keyword=""):
        st.session_state['search_type'] = mode
        st.session_state['search_keyword'] = keyword
        st.session_state['settings_expanded'] = False # 搜尋後自動收合

    def handle_custom_search():
        kw = st.session_state.kw_input
        if kw:
            set_search("custom", kw)

    # ================= 頂部設定面板 (Smart Expander) =================
    with st.expander("⚙️ 戰情室設定 (點擊展開/收合)", expanded=st.session_state['settings_expanded']):
        
        st.caption("1. 選擇時間範圍")
        # Time Grid Row 1
        time_opts_row1 = [("24H", 1), ("3天", 3), ("1週", 7), ("2週", 14)]
        r1_cols = st.columns(4)
        for idx, (lbl, val) in enumerate(time_opts_row1):
            with r1_cols[idx]:
                b_type = "primary" if st.session_state['days_int'] == val else "secondary"
                if st.button(lbl, key=f"t_{val}", type=b_type, use_container_width=True):
                    st.session_state['days_int'] = val
                    st.rerun()
        
        # Time Grid Row 2
        time_opts_row2 = [("1月", 30), ("2月", 60), ("3月", 90), ("6月", 180)]
        r2_cols = st.columns(4)
        for idx, (lbl, val) in enumerate(time_opts_row2):
            with r2_cols[idx]:
                b_type = "primary" if st.session_state['days_int'] == val else "secondary"
                if st.button(lbl, key=f"t_{val}", type=b_type, use_container_width=True):
                    st.session_state['days_int'] = val
                    st.rerun()

        st.markdown("---") # 分隔線 (設定區內保留分隔線較清楚)

        # Topic Buttons
        st.caption("2. 選擇掃描主題")
        c1, c2, c3 = st.columns(3) # 改為橫排三欄，節省垂直空間
        with c1: st.button("泰國政經情勢", use_container_width=True, on_click=set_search, args=("macro",))
        with c2: st.button("電子產業趨勢", use_container_width=True, on_click=set_search, args=("industry",))
        with c3: st.button("重點台商動態", use_container_width=True, on_click=set_search, args=("vip",))
        
        st.markdown("---")
        
        # Custom Search
        st.caption("3. 深度關鍵字追蹤")
        st.text_input("輸入關鍵字 (如: Delta)", key="kw_input", on_change=handle_custom_search)
        
        kw_val = st.session_state.get("kw_input", "")
        if kw_val:
            st.button(f"🔍 搜尋: {kw_val}", type="primary", use_container_width=True, on_click=handle_custom_search)

    # 準備搜尋參數
    days_int = st.session_state['days_int']
    # 簡單計算 label
    all_time_labels = {1:"24H", 3:"3天", 7:"1週", 14:"2週", 30:"1月", 60:"2月", 90:"3月", 180:"6月"}
    selected_label = all_time_labels.get(days_int, f"{days_int}天")
    # 移除原本的 columns 佈局，直接使用全寬
    s_type = st.session_state.get('search_type')
    s_kw = st.session_state.get('search_keyword')

    # 尚未搜尋時的歡迎畫面
    if not s_type:
        st.info("� 請展開上方的「戰情室設定」面板，開始您的產業分析。")
        st.markdown("""
        #### 歡迎來到 ThaiNews.Ai 🇹🇭
        
        這是一個專為 **泰國市場分析** 打造的 AI 戰情室。
        我們採用了 **頂部收合式** 設計，讓您在手機與電腦上都能擁有最佳閱讀體驗。
        
        **功能介紹：**
        *   **泰國政經情勢**：快速掌握大選、政策與雙邊關係。
        *   **電子產業趨勢**：專注 PCB 與電子製造供應鏈情報。
        *   **重點台商動態**：追蹤由台灣前往泰國佈局的指標企業。
        """)
    
    # 根據狀態執行邏輯
    elif s_type == "custom" and s_kw:
        st.markdown(f"##### 🔍 搜尋結果: {s_kw}")
        with st.spinner(f"正在全網搜索 {s_kw}..."):
            prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "custom", s_kw)
            display_results(prompt, news_list)
            
    elif s_type == "macro":
        st.markdown("##### 🇹🇭 泰國政經情勢")
        with st.spinner("正在掃描泰國大選、經貿與台泰新聞..."):
            prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "macro")
            display_results(prompt, news_list)
            
    elif s_type == "industry":
        st.markdown("##### 🔌 電子產業趨勢")
        with st.spinner("正在掃描 PCB 與電子供應鏈新聞..."):
            prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "industry")
            display_results(prompt, news_list)
            
    elif s_type == "vip":
        st.markdown("##### 🏢 重點台商動態")
        with st.spinner("正在掃描重點台商動態..."):
            prompt, news_list = generate_chatgpt_prompt(selected_label, days_int, "vip")
            display_results(prompt, news_list)

with tab2:
    if st.button("🔄 刷新列表"): st.rerun()
    
    if os.path.exists('news_data.json'):
        with open('news_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        news_list = data.get('news_list', [])
        st.caption(f"📅 上次更新: {data.get('timestamp', '未知')} (共 {len(news_list)} 則)")

        search_query = st.text_input("🔍 搜尋歷史...", placeholder="關鍵字")
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
            st.warning("無資料")
    else:
        st.info("尚無紀錄")
