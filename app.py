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
    /* 標題樣式 */
    .big-font { font-size: 28px !important; font-weight: 800; color: #1a1a1a; margin-bottom: 20px !important; }
    
    /* 調整垂直間距，讓畫面緊湊 */
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    
    /* 左側按鈕區專用樣式 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        font-weight: 600;
        border: 1px solid #e0e0e0;
        text-align: left; /* 讓文字靠左，像選單 */
        padding-left: 20px;
        transition: all 0.2s;
        margin-bottom: 8px;
    }
    .stButton>button:hover {
        border-color: #d93025;
        color: #d93025;
        background-color: #fff5f5;
        padding-left: 25px; /* 滑鼠移過去稍微右移，增加互動感 */
    }
    
    /* 新聞卡片樣式 */
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
</style>
""", unsafe_allow_html=True)

# ================= 爬蟲核心邏輯 =================

def get_rss_sources(days, mode="all", custom_keyword=None):
    sources = []
    
    if mode == "custom" and custom_keyword:
        clean_keyword = custom_keyword.strip().replace(" ", "+")
        sources.append({
            "name": f"🔍 深度追蹤: {custom_keyword}",
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
            {"name": "🇹🇭 泰國整體 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"},
            {"name": "🇹🇭 泰國整體 (中)", "url": f"https://news.google.com/rss/search?q=泰國+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"},
            {"name": "🇹🇼 台泰關係 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+Taiwan+OR+%22Taiwanese+investment%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"},
            {"name": "🇹🇼 台泰關係 (中)", "url": f"https://news.google.com/rss/search?q=泰國+台灣+OR+%22台商%22+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"}
        ])
    elif mode == "industry":
        sources.extend([
            {"name": "🔌 PCB製造 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+%22Electronics+Manufacturing%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"},
            {"name": "🔌 PCB製造 (中)", "url": f"https://news.google.com/rss/search?q=泰國+PCB+OR+%22電子製造%22+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"}
        ])
    elif mode == "vip":
        sources.extend([
            {"name": "🏢 台商動態 (EN)", "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+{vip_query_en}+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"},
            {"name": "🏢 台商動態 (中)", "url": f"https://news.google.com/rss/search?q=泰國+OR+{vip_query_cn}+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"}
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
                limit = 30 
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
    
    return output_text

# ================= 網頁主程式 =================

st.markdown('<div class="big-font">ThaiNews.Ai 🇹🇭 戰情室</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🤖 生成器", "📊 歷史庫"])

with tab1:
    # --- 頂部設定區 (全寬) ---
    col_top_1, col_top_2 = st.columns([2, 3])
    with col_top_1:
        time_options = { "24H": 1, "3天": 3, "1週": 7, "2週": 14, "1月": 30 }
        selected_label = st.radio("時間區間", options=list(time_options.keys()), horizontal=True, label_visibility="collapsed")
        days_int = time_options[selected_label]
    with col_top_2:
        custom_keyword = st.text_input("🔍 自訂搜尋 (選填)", placeholder="例如: Delta, CP Group...", label_visibility="collapsed")
    
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True) # 細分隔線

    # --- 核心佈局：左導航 (1) vs 右內容 (3) ---
    col_left, col_right = st.columns([1, 3], gap="medium")

    # [左側] 按鈕選單區
    with col_left:
        st.caption("👇 選擇情報主題")
        
        # 如果有輸入自訂關鍵字，就顯示自訂搜尋按鈕
        if custom_keyword.strip():
            btn_custom = st.button(f"🔍 搜尋: {custom_keyword}", type="primary")
        else:
            btn_custom = False

        btn_macro = st.button("🇹🇭 1. 宏觀戰情")
        btn_industry = st.button("🔌 2. 產業戰情")
        btn_vip = st.button("🏢 3. 台商戰情")

    # [右側] 內容顯示區
    with col_right:
        # 根據按下的按鈕觸發邏輯
        if btn_custom:
            with st.spinner(f"正在全網搜索 {custom_keyword}..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "custom", custom_keyword)
                st.success(f"🎉 [{custom_keyword}] 報告生成成功！")
                st.code(prompt, language="markdown")
                
        elif btn_macro:
            with st.spinner("正在掃描 泰國政經與台泰關係..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "macro")
                st.success("🎉 宏觀報告生成成功！")
                st.code(prompt, language="markdown")
                
        elif btn_industry:
            with st.spinner("正在掃描 PCB 供應鏈動態..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "industry")
                st.success("🎉 產業報告生成成功！")
                st.code(prompt, language="markdown")
                
        elif btn_vip:
            with st.spinner("正在掃描 重點台商清單..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "vip")
                st.success("🎉 台商報告生成成功！")
                st.code(prompt, language="markdown")
        else:
            # 預設顯示畫面 (還沒按按鈕時)
            st.info("👈 請點擊左側按鈕開始生成情報。")
            st.markdown(
                """
                <div style="color: #666; font-size: 14px;">
                <b>操作說明：</b><br>
                1. 在上方選擇 <b>時間區間</b>。<br>
                2. (選填) 輸入 <b>公司名稱</b> 可進行自訂搜尋。<br>
                3. 點擊 <b>左側主題按鈕</b>，AI 將自動抓取並生成分析指令。
                </div>
                """, unsafe_allow_html=True
            )

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
