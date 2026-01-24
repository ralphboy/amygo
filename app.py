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

def get_rss_sources(days, custom_keyword=None, category_mode=None):
    sources = []
    
    # === 模式 A：深度鑽研 (只搜自訂) ===
    if custom_keyword and custom_keyword.strip():
        clean_keyword = custom_keyword.strip().replace(" ", "+")
        sources.append({
            "name": f"🔍 深度追蹤: {custom_keyword} (EN)",
            "url": f"https://news.google.com/rss/search?q={clean_keyword}+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
        })
        sources.append({
            "name": f"🔍 深度追蹤: {custom_keyword} (中文)",
            "url": f"https://news.google.com/rss/search?q={clean_keyword}+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        })
        return sources

    # === 模式 B：廣度掃描 (區分類別) ===
    
    # 定義各類別的 URL
    
    # 1. General & Relations
    src_general_en = {
        "name": "🇹🇭 1. 泰國整體重要新聞 (EN)", 
        "url": f"https://news.google.com/rss/search?q=Thailand+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
    }
    src_general_cn = {
        "name": "🇹🇭 1. 泰國整體重要新聞 (中文)", 
        "url": f"https://news.google.com/rss/search?q=泰國+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    }
    src_relations_en = {
        "name": "🇹🇼 2. 台泰關係 (EN)", 
        "url": f"https://news.google.com/rss/search?q=Thailand+Taiwan+OR+%22Taiwanese+investment%22+OR+%22Taiwan+companies%22+OR+%22Trade+Relations%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
    }
    src_relations_cn = {
        "name": "🇹🇼 2. 台泰關係 (中文)", 
        "url": f"https://news.google.com/rss/search?q=泰國+台灣+OR+%22台商%22+OR+%22投資%22+OR+%22經貿%22+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    }

    # 2. PCB & Electronics
    src_pcb_en = {
        "name": "🔌 3. PCB 與電子製造 (EN)", 
        "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+%22Printed+Circuit+Board%22+OR+%22Electronics+Manufacturing%22+OR+%22Server+Production%22+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
    }
    src_pcb_cn = {
        "name": "🔌 3. PCB 與電子製造 (中文)", 
        "url": f"https://news.google.com/rss/search?q=泰國+PCB+OR+%22印刷電路板%22+OR+%22電子製造%22+OR+%22伺服器%22+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    }

    # 3. VIP Companies
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

    src_vip_en = {
        "name": "🏢 4. 重點台商動態追蹤 (EN)",
        "url": f"https://news.google.com/rss/search?q=Thailand+PCB+OR+{vip_query_en}+when:{days}d&hl=en-TH&gl=TH&ceid=TH:en"
    }
    src_vip_cn = {
        "name": "🏢 4. 重點台商動態追蹤 (中文)",
        "url": f"https://news.google.com/rss/search?q=泰國+OR+{vip_query_cn}+when:{days}d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    }

    # === 根據 category_mode 回傳對應清單 ===
    if category_mode == 'general':
        return [src_general_en, src_general_cn, src_relations_en, src_relations_cn]
    
    elif category_mode == 'pcb':
        return [src_pcb_en, src_pcb_cn]
        
    elif category_mode == 'vip':
        return [src_vip_en, src_vip_cn]
    
    else:
        # Fallback (全部回傳，如果不小心沒指定模式)
        return [
            src_general_en, src_general_cn, 
            src_relations_en, src_relations_cn,
            src_pcb_en, src_pcb_cn,
            src_vip_en, src_vip_cn
        ]

def generate_chatgpt_prompt(days_label, days_int, custom_keyword, category_mode=None):
    status_text = st.empty() 
    progress_bar = st.progress(0)
    
    sources = get_rss_sources(days_int, custom_keyword, category_mode)
    
    news_items_for_json = []

    # === 生成 Prompt (針對不同按鈕客製化角色與指令) ===
    if custom_keyword and custom_keyword.strip():
        # 自訂搜尋模式
        role = "產業分析師"
        focus = f"針對關鍵字【{custom_keyword}】"
        instruction = "請撰寫一份「深度主題分析報告」，包含：重點摘要、市場影響、潛在機會與風險。"
    
    elif category_mode == 'general':
        # 1. 泰國整體 + 台泰關係
        role = "泰國政經觀察家"
        focus = f"【{days_label} 泰國政經局勢與台泰關係】"
        instruction = """
請重點分析：
1. 泰國重大政治與經濟政策變動。
2. 台泰雙邊關係、經貿互動或投資新訊。
3. 社會安全或旅遊相關的重要影響。
"""
    elif category_mode == 'pcb':
        # 2. PCB 電子製造
        role = "電子供應鏈專家"
        focus = f"【{days_label} 泰國 PCB 與電子製造業情報】"
        instruction = """
請重點分析：
1. PCB 產業在泰國的擴廠、投資動態。
2. 上下游供應鏈的聚落變化。
3. 伺服器與消費電子的生產趨勢。
"""
    elif category_mode == 'vip':
        # 3. 重點台商
        role = "科技產業證券分析師"
        focus = f"【{days_label} 重點台商與科技大廠動態】"
        instruction = """
目標公司：台達電、鴻海、英業達、臻鼎、欣興、華通、金像電、健鼎、定穎、燿華。
請重點分析：
1. 個別公司在泰國的新聞、擴產或營運狀況。
2. 競爭對手或合作夥伴的相關消息。
3. 股價或營收相關的當地報導（若有）。
"""
    else:
        # Fallback
        role = "東南亞產經分析師"
        focus = "泰國產業新聞"
        instruction = "請分析：1.泰國整體 2.電子製造 3.台泰關係 4.台商動態"

    instruction_prompt = f"""
請扮演一位資深的「{role}」。
以下是{focus}的新聞資料庫（中英雙語）。
{instruction}
"""

    output_text = f"""
{instruction_prompt}

請用**繁體中文**，並以 **Markdown** 條列式輸出，風格需專業且易讀。

========= 以下是新聞資料庫 ({datetime.now().strftime('%Y-%m-%d')}) =========
"""
    
    seen_titles = set()
    total_steps = len(sources)
    
    for i, source in enumerate(sources):
        status_text.text(f"📡 正在掃描: {source['name']} ...")
        
        try:
            feed = feedparser.parse(source['url'])
            
            if len(feed.entries) > 0:
                output_text += f"\n## 【{source['name']}】\n"
                
                # 因為拆成不同按鈕，每個類別的新聞量可以放寬，讓 User 不怕漏新聞
                limit = 25 
                
                for entry in feed.entries[:limit]: 
                    if entry.title in seen_titles: continue
                    seen_titles.add(entry.title)
                    
                    source_name = entry.source.title if 'source' in entry else "Google News"
                    pub_date = entry.published if 'published' in entry else ""
                    
                    # 1. 加入 Prompt
                    output_text += f"- [{pub_date}] [{source_name}] {entry.title}\n  連結: {entry.link}\n"
                    
                    # 2. 加入 JSON 存檔
                    news_items_for_json.append({
                        "title": entry.title,
                        "link": entry.link,
                        "date": pub_date,
                        "source": source_name,
                        "category": source['name']
                    })
            else:
                output_text += f"\n## 【{source['name']}】\n(無相關新聞)\n"

        except Exception as e:
            st.error(f"抓取錯誤: {e}")
        
        progress_bar.progress((i + 1) / total_steps)
        time.sleep(0.5)

    output_text += "\n========= 資料結束 ========="
    
    # === 儲存至 JSON ===
    # 注意：這裡使用 'a' (append) 模式可能更難管理，我們維持 'w' 覆寫，但 User 應知曉
    # 若要保留所有類別，可能需要先讀取再合併，但為了 Prompt 生成的一致性，
    # 這裡的邏輯是「最後一次搜尋的內容」會顯示在 Tab 2。
    # 為了良好的 UX，我們在 Tab 2 可能需要說「顯示最近一次搜尋結果」。
    
    try:
        with open('news_data.json', 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "news_list": news_items_for_json
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"存檔失敗: {e}")

    status_text.text("✅ 抓取完成！資料已存入歷史庫。")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    
    return output_text

# ================= 網頁主程式 =================

st.markdown('<div class="big-font">ThaiNews.Ai 🇹🇭 戰情室</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🤖 ChatGPT 懶人包 (生成器)", "📊 歷史新聞庫 (可搜尋)"])

# --- Tab 1 ---
with tab1:
    st.markdown("### 🚀 一鍵生成 ChatGPT 分析指令")
    
    time_options = {
        "1 天 (24h)": 1,
        "3 天": 3,
        "1 週 (7天)": 7,
        "2 週 (14天)": 14,
        "1 個月 (30天)": 30
    }
    selected_label = st.radio(
        "選擇新聞區間",
        options=list(time_options.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )
    days_int = time_options[selected_label]

    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        custom_keyword = st.text_input(
            "🔍 自訂搜尋關鍵字 (選填)", 
            placeholder="例如: \"Delta Electronics\" -Airline"
        )
    with col2:
        st.write("") 
        st.caption("⚠️ 輸入後將只搜尋此關鍵字。")

    st.markdown("---")
    
    if custom_keyword:
        if st.button(f"🔍 開始深度搜尋: {custom_keyword}", type="primary"):
            with st.spinner(f"正在全網搜索..."):
                prompt_content = generate_chatgpt_prompt(selected_label, days_int, custom_keyword)
                st.success("🎉 生成成功！請點擊下方區塊右上角複製。")
                st.code(prompt_content, language="markdown")
    else:
        st.markdown("#### 請選擇搜尋主題：")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if st.button("🇹🇭 1. 政經局勢 + 台泰關係", type="primary"):
                 with st.spinner("正在掃描泰國大選、經貿與台泰新聞..."):
                    prompt_content = generate_chatgpt_prompt(selected_label, days_int, None, category_mode='general')
                    st.success("政經情勢報告指令生成完畢！")
                    st.code(prompt_content, language="markdown")
        
        with c2:
            if st.button("🔌 2. PCB 與電子製造", type="secondary"):
                with st.spinner("正在掃描 PCB 與電子供應鏈新聞..."):
                    prompt_content = generate_chatgpt_prompt(selected_label, days_int, None, category_mode='pcb')
                    st.success("電子產業報告指令生成完畢！")
                    st.code(prompt_content, language="markdown")
                    
        with c3:
            if st.button("🏢 3. 重點台商動態", type="secondary"):
                with st.spinner("正在掃描 10 大重點台商新聞..."):
                    prompt_content = generate_chatgpt_prompt(selected_label, days_int, None, category_mode='vip')
                    st.success("台商監測報告指令生成完畢！")
                    st.code(prompt_content, language="markdown")

# --- Tab 2 (大改版：新增搜尋與卡片) ---
with tab2:
    st.markdown("### 📂 本地資料庫檢視")
    
    if os.path.exists('news_data.json'):
        with open('news_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        last_update = data.get('timestamp', '未知')
        news_list = data.get('news_list', [])
        
        # 1. 頂部資訊列
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.info(f"📅 上次更新時間: **{last_update}** (共 {len(news_list)} 則)")
        with col_b:
            if st.button("🔄 重新載入"):
                st.rerun()

        # 2. 🔍 搜尋篩選器 (關鍵新功能)
        search_query = st.text_input("🔍 在歷史紀錄中搜尋...", placeholder="輸入關鍵字 (例如: PCB, EV, Investment)")

        # 3. 篩選邏輯
        if search_query:
            # 只顯示標題包含關鍵字的新聞
            filtered_list = [n for n in news_list if search_query.lower() in n['title'].lower()]
            st.caption(f"找到 {len(filtered_list)} 則關於「{search_query}」的新聞：")
        else:
            filtered_list = news_list

        # 4. 卡片顯示 (美化版 + 防呆)
        if len(filtered_list) > 0:
            for news in filtered_list:
                # [修正] 使用 .get() 防止舊資料報錯
                category_label = news.get('category', '歷史新聞')
                
                st.markdown(f"""
                <div class="news-card">
                    <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                    <div class="news-meta">
                        {news['date']} • {news['source']}
                        <span class="news-tag">{category_label}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 找不到符合搜尋條件的新聞。")

    else:
        st.warning("📭 目前沒有歷史紀錄，請先在【生成器】分頁執行搜尋。")
