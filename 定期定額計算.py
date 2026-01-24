import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import webbrowser
import os
import numpy as np

def calculate_strategy(df, weekday_target, weekly_budget):
    """
    weekday_target: 0=Mon, 2=Wed, 4=Fri
    邏輯：產生該週間的目標日期列表，並在 dataframe 中尋找最近的交易日
    """
    # 產生從資料起始日到結束日的所有「目標星期幾」
    start_date = df.index[0]
    end_date = df.index[-1]
    
    # pandas 的 date_range 可以設定頻率，例如 'W-MON' (每週一)
    freq_map = {0: 'W-MON', 2: 'W-WED', 4: 'W-FRI'}
    target_dates = pd.date_range(start=start_date, end=end_date, freq=freq_map[weekday_target])
    
    total_invested = 0
    total_shares = 0
    
    # 使用 searchsorted 快速找到「大於等於目標日期」的第一個交易日索引
    # 這能自動處理「遇到假日順延買進」的邏輯
    valid_indices = df.index.searchsorted(target_dates)
    
    # 過濾掉超出範圍的索引 (防止目標日期剛好在最後一天之後)
    valid_indices = valid_indices[valid_indices < len(df)]
    
    # 取得這些日期的股價
    buy_prices = df.iloc[valid_indices]['Close']
    
    for price in buy_prices:
        if price > 0:
            total_shares += weekly_budget / price
            total_invested += weekly_budget
            
    current_price = df.iloc[-1]['Close']
    final_value = total_shares * current_price
    roi = (final_value - total_invested) / total_invested * 100 if total_invested > 0 else 0
    
    return roi, total_invested, final_value

def compare_weekly_dca():
    print("\n" + "="*50)
    print(" 📅 每週定期定額大對決：週一 vs 週三 vs 週五")
    print("="*50)
    
    try:
        start_year_input = input("請輸入開始年份 (例如 2016): ").strip()
        weekly_budget = 2500 # 固定題目要求的 2500
        start_year = int(start_year_input)
        target_start_date = datetime(start_year, 1, 1)
        
        if target_start_date > datetime.now():
            print("❌ 年份錯誤")
            return
            
    except ValueError:
        print("❌ 請輸入數字")
        return

    portfolio = {
        '台積電': '2330.TW',
        '鴻海': '2317.TW',
        '台達電': '2308.TW',
        '富邦未來車': '00895.TW', 
        '野村新科技': '00935.TW',
    }
    
    results = []
    print(f"\n🚀 正在運算中 (每週投入 ${weekly_budget})...")
    
    for name, ticker in portfolio.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=target_start_date - relativedelta(months=1), auto_adjust=True)
            
            if hist.empty:
                print(f"⚠️ {name} 無資料，跳過")
                continue

            df = hist[['Close']].copy()
            
            # 確保起始時間正確
            actual_start = df.index[0]
            target_start_tz = target_start_date.replace(tzinfo=actual_start.tzinfo)
            start_date = max(target_start_tz, actual_start)
            df = df[df.index >= start_date].copy()
            
            if df.empty: continue

            # --- 計算三種策略 ---
            roi_mon, cost, val_mon = calculate_strategy(df, 0, weekly_budget) # 週一
            roi_wed, _, val_wed   = calculate_strategy(df, 2, weekly_budget) # 週三
            roi_fri, _, val_fri   = calculate_strategy(df, 4, weekly_budget) # 週五
            
            # 找出贏家
            rois = {'週一': roi_mon, '週三': roi_wed, '週五': roi_fri}
            winner = max(rois, key=rois.get)
            diff = max(rois.values()) - min(rois.values())
            
            results.append({
                '股票名稱': name,
                '投資年數': f"{(df.index[-1] - df.index[0]).days / 365.25:.1f} 年",
                '週一報酬率': roi_mon,
                '週三報酬率': roi_wed,
                '週五報酬率': roi_fri,
                '最佳買點': winner,
                '差異幅度': diff
            })
            
        except Exception as e:
            print(f"❌ {name} 錯誤: {e}")

    # --- 產生 HTML ---
    if not results: return

    df_res = pd.DataFrame(results)
    
    # 格式化
    df_disp = df_res.copy()
    for col in ['週一報酬率', '週三報酬率', '週五報酬率']:
        df_disp[col] = df_disp[col].apply(lambda x: f"{x:+.2f}%")
    
    df_disp['差異幅度'] = df_disp['差異幅度'].apply(lambda x: f"{x:.2f}%")

    # CSS 特別標註贏家
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>每週買進策略回測</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; padding: 40px; background: #f4f4f9; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: #5e63b6; color: white; padding: 12px; }}
            td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: center; }}
            tr:hover {{ background-color: #f1f1f1; }}
            .winner {{ color: #d0021b; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 每週 $2,500 買進策略比較</h1>
            <p style="text-align:center">回測起始年份: {start_year} | 標的差異分析</p>
            {df_disp.to_html(index=False, classes='table', border=0)}
            <p><i>*註：若遇休市，系統會自動在下一個交易日買進。</i></p>
        </div>
    </body>
    </html>
    """
    
    with open("weekly_dca_report.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"\n✅ 分析完成！已開啟報表。")
    webbrowser.open('file://' + os.path.realpath("weekly_dca_report.html"))

if __name__ == "__main__":
    compare_weekly_dca()