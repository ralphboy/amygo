import feedparser
import requests
import json
import time
from datetime import datetime

# =================設定區=================
API_KEY = "AIzaSyCUmsAZ52fpN44LegDnhHo-0Sf6cQOltes" 
MODEL_NAME = "gemini-3-flash-preview"

# 設定三大追蹤目標 (搜尋過去 24 小時 when:1d)
RSS_SOURCES = [
    # 1. 泰國整體商業環境
    {
        "name": "🇹🇭 Thailand Business", 
        "url": "https://news.google.com/rss/search?q=Thailand+Business+OR+Economy+when:1d&hl=en-TH&gl=TH&ceid=TH:en"
    },
    # 2. PCB 與電子製造 (擴充關鍵字以免 PCB 當天沒新聞抓不到)
    {
        "name": "🔌 Thailand PCB/Electronics", 
        "url": "https://news.google.com/rss/search?q=Thailand+PCB+OR+%22Printed+Circuit+Board%22+OR+%22Electronics+Manufacturing%22+when:1d&hl=en-TH&gl=TH&ceid=TH:en"
    },
    # 3. 台泰關係與台商動態
    {
        "name": "🇹🇼 Thailand-Taiwan Relations", 
        "url": "https://news.google.com/rss/search?q=Thailand+Taiwan+OR+%22Taiwanese+investment%22+OR+%22Taiwan+companies%22+when:1d&hl=en-TH&gl=TH&ceid=TH:en"
    }
]
# =======================================

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception:
        pass
    return None

def generate_executive_summary(all_news_titles):
    print("\n🧠 AI 總編輯正在分析【PCB 供應鏈】與【台泰商機】...")
    
    prompt = f"""
    你是專精於「泰國電子供應鏈」與「台泰經貿」的資深商業顧問。
    以下是過去 24 小時內，針對 Thailand Business, PCB Industry, 及 Taiwan-Thailand Relations 的聚合新聞。
    
    請撰寫一份「泰國 PCB 與台商每日情報」報告。

    新聞標題列表：
    {all_news_titles}

    請依照以下 Markdown 格式輸出：

    # 🇹🇭 泰國 PCB 與台商每日情報 ({datetime.now().strftime('%Y-%m-%d')})

    ## 🎯 戰略洞察 (Executive Summary)
    (請綜合分析今日局勢，特別著重於電子產業供應鏈變化、以及台商在泰國的新機會或挑戰。)

    ## 🔌 PCB 與電子產業焦點
    (請挑選最重要的相關新聞，若無特定 PCB 新聞，則分析整體電子製造業趨勢)
    * **[新聞標題]**：事件摘要與供應鏈影響。

    ## 🇹🇼 台泰經貿與台商動態
    * **[新聞標題]**：分析這對在泰台商有何意義。

    ## 💰 泰國總體經濟環境
    * (簡述政策、匯率或基礎建設等大環境變化)

    ---
    *註：本報告由 Gemini 3 AI 自動彙整分析*
    """
    return call_gemini(prompt)

def get_thai_news():
    all_raw_news = []
    processed_news = []
    seen_titles = set()
    
    print("🚀 啟動戰情爬蟲 (Target: PCB & Taiwan-Thailand)...")

    for source in RSS_SOURCES:
        print(f"📡 正在監控: {source['name']} ...")
        
        feed = feedparser.parse(source['url'])
        
        if len(feed.entries) == 0:
            print(f"   ⚠️ 無今日新聞 (可能該領域今日無重大消息)")
            continue
            
        print(f"   ✅ 發現 {len(feed.entries)} 則情報")
            
        # 每個分類抓前 10 則
        for entry in feed.entries[:10]:
            if entry.title in seen_titles:
                continue
            seen_titles.add(entry.title)

            clean_title = entry.title
            media_source = entry.source.title if 'source' in entry else "Google News"

            all_raw_news.append(f"- [{source['name']}] {clean_title}")
            
            processed_news.append({
                "source": source['name'], # 標記是哪一類的新聞 (PCB/Taiwan/Business)
                "title": clean_title,
                "link": entry.link,
                "date": entry.published if 'published' in entry else datetime.now().strftime("%Y-%m-%d"),
            })
        
        time.sleep(0.5)

    if not all_raw_news:
        print("❌ 今日三大領域皆無新聞。")
        return

    print(f"\n📦 共收集到 {len(all_raw_news)} 則關鍵情報，開始戰略分析...")
    executive_summary = generate_executive_summary("\n".join(all_raw_news))
    
    if not executive_summary:
        executive_summary = "AI 無法生成報告。"

    final_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "executive_summary": executive_summary,
        "news_list": processed_news
    }

    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    
    print("\n🎉 戰情報告已生成！請刷新網頁查看。")

if __name__ == "__main__":
    get_thai_news()