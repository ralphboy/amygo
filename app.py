import streamlit as st
import json
import os
import html
import logic  # Refactored logic module

# ================= 1. 頁面設定 (必須放第一行) =================
st.set_page_config(
    page_title="Amy 的印尼研究院", 
    page_icon="🇮🇩", 
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

# 套用 CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ================= 3. UI 輔助函式 =================

def display_results(prompt, news_list):
    """顯示搜尋結果的共用函數"""
    st.markdown("##### 1. AI 分析指令")
    with st.expander("點擊展開查看 Prompt", expanded=True):
        st.code(prompt, language="markdown")
        
    st.markdown("##### 2. 相關新聞速覽")
    if news_list:
        for news in news_list:
            cat = news.get('category', '一般')
            # Security fix: Escape HTML special characters
            safe_title = html.escape(news['title'])
            safe_source = html.escape(news['source'])
            
            st.markdown(f'''
            <div class="news-card">
                <a href="{news['link']}" target="_blank" class="news-title">{safe_title}</a>
                <div class="news-meta">{news['date']} • {safe_source} <span class="news-tag">{cat}</span></div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.warning("查無新聞資料。")

# ================= 4. 網頁主程式 =================

st.markdown('<div class="big-font">Amy 的印尼研究院</div>', unsafe_allow_html=True)

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
            date_selection = st.pills("Time", list(logic.DATE_MAP.keys()), default="3天", label_visibility="collapsed", key="pills_date")
        except AttributeError:
            st.error("請更新 Streamlit 版本至 1.40+ 以使用 Pills 元件，或改用 Radio。")
            date_selection = st.radio("Time", list(logic.DATE_MAP.keys()), horizontal=True, label_visibility="collapsed")
            
        if date_selection:
            st.session_state['days_int'] = logic.DATE_MAP[date_selection] 

        # 2. 主題選擇
        st.caption("2. 分析主題")
        try:
            topic_selection = st.pills("Topic", list(logic.TOPIC_MAP.keys()), label_visibility="collapsed", selection_mode="single", key="pills_topic")
        except AttributeError:
            topic_selection = st.radio("Topic", ["(請選擇)"] + list(logic.TOPIC_MAP.keys()), label_visibility="collapsed")
            if topic_selection == "(請選擇)": topic_selection = None
        
        if topic_selection:
            target_mode = logic.TOPIC_MAP[topic_selection]
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
        selected_label = next((k for k, v in logic.DATE_MAP.items() if v == days_int), f"{days_int}天")
        
        s_type = st.session_state.get('search_type')
        s_kw = st.session_state.get('search_keyword')

        # 尚未搜尋時的歡迎畫面
        if not s_type:
            st.info("👈 請從左側選擇主題或輸入關鍵字開始。")
            st.markdown("""
            <div style="background:#f8f9fa; padding:15px; border-radius:10px; color:#555;">
                <strong>💡 系統說明：</strong><br>
                1. <b>印尼政經</b>：政經局勢與台印關係 (含新首都進度)。<br>
                2. <b>電動車與供應鏈</b>：EV、電池、鎳礦與電子製造。<br>
                3. <b>重點台商</b>：鎖定 10+ 大指標台廠 (Foxconn, Pegatron, etc.) 動態。
            </div>
            """, unsafe_allow_html=True)
        
        # 執行搜尋
        else:
            if s_type == "custom" and s_kw:
                with st.spinner(f"正在全網搜索 {s_kw}..."):
                    prompt, news_list = logic.generate_chatgpt_prompt(selected_label, days_int, "custom", s_kw)
                    display_results(prompt, news_list)
                    
            elif s_type == "macro":
                with st.spinner("正在掃描印尼大選、經貿與台印新聞..."):
                    prompt, news_list = logic.generate_chatgpt_prompt(selected_label, days_int, "macro")
                    display_results(prompt, news_list)
                    
            elif s_type == "industry":
                with st.spinner("正在掃描印尼EV與電子產業新聞..."):
                    prompt, news_list = logic.generate_chatgpt_prompt(selected_label, days_int, "industry")
                    display_results(prompt, news_list)
                    
            elif s_type == "vip":
                with st.spinner("正在掃描重點台商動態..."):
                    prompt, news_list = logic.generate_chatgpt_prompt(selected_label, days_int, "vip")
                    display_results(prompt, news_list)

with tab2:
    col_head_1, col_head_2 = st.columns([3, 1])
    with col_head_1:
        st.markdown("### 📂 歷史新聞資料庫")
    with col_head_2:
        if st.button("🔄 刷新列表"): st.rerun()
    
    if os.path.exists('news_data.json'):
        with open('news_data.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        
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