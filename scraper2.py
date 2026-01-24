import feedparser
import time
from datetime import datetime, timedelta

# =================設定區=================
# 設定搜尋範圍：過去 14 天 (when:14d)
# 針對三大戰略方向設定精準關鍵字
RSS_SOURCES = [
    {
        "name": "🇹🇭 1. 泰國整體重要新聞 (General News)", 
        # 搜尋泰國整體大新聞，排除過於瑣碎的內容
        "url": "https://news.google.com/rss/search?q=Thailand+when:14d&hl=en-TH&gl=TH&ceid=TH:en"
    },
    {
        "name": "🔌 2. PCB 與電子製造 (PCB & Electronics)", 
        # 鎖定 PCB、電路板、電子製造、伺服器供應鏈
        "url": "https://news.google.com/rss/search?q=Thailand+PCB+OR+%22Printed+Circuit+Board%22+OR+%22Electronics+Manufacturing%22+OR+%22Server+Production%22+when:14d&hl=en-TH&gl=TH&ceid=TH:en"
    },
    {
        "name": "🇹🇼 3. 台泰關係 (Taiwan-Thailand Relations)", 
        # 鎖定台灣投資、台商、雙邊關係
        "url": "https://news.google.com/rss/search?q=Thailand+Taiwan+OR+%22Taiwanese+investment%22+OR+%22Taiwan+companies%22+OR+%22Trade+Relations%22+when:14d&hl=en-TH&gl=TH&ceid=TH:en"
    }
]
# =======================================

def get_thai_news():
    print(f"🚀 啟動兩週戰情抓取器 ({datetime.now().strftime('%Y-%m-%d')})...")
    
    # 自動生成給 ChatGPT 的 Prompt
    output_text = f"""
請扮演一位資深的「東南亞產經分析師」。
以下是我透過程式抓取的【過去 14 天 (近兩週) 泰國新聞資料庫】。

請閱讀這些新聞標題與來源，幫我按照以下三個方向進行「深度整理與分析」：

### 1. 🇹🇭 泰國整體重要新聞
   - 重點關注：政治動態（如選舉、內閣）、重大經濟政策、社會安全（如邊境衝突、南部動亂）。
   - 請列出最具影響力的 3-5 件大事。

### 2. 🔌 泰國 PCB 與電子製造
   - 重點關注：新廠設立（特別是 PCB 廠）、供應鏈移轉動態、大型投資案（如 AWS, Google 或台廠）。
   - 請分析這對全球電子供應鏈的意義。

### 3. 🇹🇼 台泰關係與台商動態
   - 重點關注：台灣企業在泰投資新訊、雙邊貿易協定、人才交流或地緣政治影響。
   - 請指出台商在泰國的機會或潛在風險。

請用**繁體中文**，並以 **Markdown** 條列式輸出，風格需專業且易讀。

========= 以下是近兩週新聞資料庫 =========
"""

    total_count = 0
    seen_titles = set()

    for source in RSS_SOURCES:
        print(f"📡 正在掃描: {source['name']} ...")
        feed = feedparser.parse(source['url'])
        
        if len(feed.entries) > 0:
            output_text += f"\n## 【{source['name']}】\n"
            
            count = 0
            # 兩週的新聞量較大，我們每個分類抓前 20-30 則比較剛好，避免 ChatGPT 吃不消
            for entry in feed.entries[:30]: 
                if entry.title in seen_titles:
                    continue
                seen_titles.add(entry.title)
                
                clean_title = entry.title
                source_name = entry.source.title if 'source' in entry else "Unknown"
                pub_date = entry.published if 'published' in entry else "Unknown Date"
                
                output_text += f"- [{pub_date}] [{source_name}] {clean_title}\n  連結: {entry.link}\n"
                count += 1
            
            output_text += "\n"
            total_count += count
            print(f"   ✅ 抓取 {count} 則")
        else:
            print("   ⚠️ 無資料")
        
        time.sleep(1) # 休息一下避免被擋

    output_text += "\n========= 資料結束 ========="

    filename = "chatgpt_prompt_2weeks.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output_text)

    print("-" * 30)
    print(f"🎉 成功！共整理了 {total_count} 則近兩週新聞。")
    print(f"📄 請打開左側檔案【{filename}】，全選複製並貼給 ChatGPT！")

if __name__ == "__main__":
    get_thai_news()