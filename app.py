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
    # 版面核心：左控右顯
    c_left, c_right = st.columns([1, 3], gap="medium")
    
    with c_left:
        st.markdown("##### ⚙️ 設定操作") # 簡化標題
        
        # 1. 時間選擇 (改為 4x2 按鈕網格，追求對稱美感)
        if 'days_int' not in st.session_state:
            st.session_state['days_int'] = 1 # 預設 24H

        # 定義選項：標籤 vs 天數
        time_opts_row1 = [("24H", 1), ("3天", 3), ("1週", 7), ("2週", 14)]
        time_opts_row2 = [("1月", 30), ("2月", 60), ("3月", 90), ("6月", 180)]
        
        # 建立反查表給 Prompt 使用
        all_opts = dict(time_opts_row1 + time_opts_row2)
        days_int = st.session_state['days_int']
        # 找出對應的 label，若無則預設顯示天數
        selected_label = next((k for k, v in all_opts.items() if v == days_int), f"{days_int}天")

        # Row 1
        r1_cols = st.columns(4)
        for idx, (lbl, val) in enumerate(time_opts_row1):
            with r1_cols[idx]:
                # 若被選中則亮色
                b_type = "primary" if days_int == val else "secondary"
                if st.button(lbl, key=f"t_{val}", type=b_type, use_container_width=True):
                    st.session_state['days_int'] = val
                    st.rerun()

        # Row 2 (更緊湊，減少垂直間距)
        r2_cols = st.columns(4)
        for idx, (lbl, val) in enumerate(time_opts_row2):
            with r2_cols[idx]:
                b_type = "primary" if days_int == val else "secondary"
                if st.button(lbl, key=f"t_{val}", type=b_type, use_container_width=True):
                    st.session_state['days_int'] = val
                    st.rerun()

        st.write("") # 輕微間距代替 ---

        # 2. 三大主題按鈕 (移除 caption，直接顯示)
        btn_macro = st.button("泰國政經情勢", use_container_width=True)
        btn_industry = st.button("電子產業趨勢", use_container_width=True)
        btn_vip = st.button("重點台商動態", use_container_width=True)
        
        st.write("") # 輕微間距代替 ---
        
        # 3. 自訂搜尋
        custom_keyword = st.text_input("深度追蹤", placeholder="輸入關鍵字 (如: Delta)")
        btn_custom = st.button(f"🔍 搜尋", type="primary", use_container_width=True) if custom_keyword else None

    # 右側：顯示結果區域
    with c_right:
        # 預設顯示歡迎詞或說明
        if not (btn_macro or btn_industry or btn_vip or (btn_custom and custom_keyword)):
            st.info("👈 請從左側選擇掃描主題，或輸入關鍵字進行搜尋。")
            st.markdown("""
            #### 💡 提示
            * **宏觀戰情**：涵蓋泰國政經、政策與台泰關係。
            * **產業戰情**：專注 PCB、伺服器與電子製造供應鏈。
            * **台商戰情**：鎖定 10 大重點台商 (鴻海、台達電、廣達等) 動態。
            """)
        
        # 邏輯執行
        if btn_custom and custom_keyword:
            st.markdown(f"#### 🔍 搜尋結果: {custom_keyword}")
            with st.spinner("正在全網搜索..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "custom", custom_keyword)
                st.success("生成完成！")
                st.code(prompt, language="markdown")
                
        elif btn_macro:
            st.markdown("#### 🇹🇭 宏觀戰情報告")
            with st.spinner("正在掃描泰國大選、經貿與台泰新聞..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "macro")
                st.success("生成完成！")
                st.code(prompt, language="markdown")
                
        elif btn_industry:
            st.markdown("#### 🔌 產業戰情報告")
            with st.spinner("正在掃描 PCB 與電子供應鏈新聞..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "industry")
                st.success("生成完成！")
                st.code(prompt, language="markdown") 
                
        elif btn_vip:
            st.markdown("#### 🏢 台商戰情報告")
            with st.spinner("正在掃描重點台商動態..."):
                prompt = generate_chatgpt_prompt(selected_label, days_int, "vip")
                st.success("生成完成！")
                st.code(prompt, language="markdown")

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
