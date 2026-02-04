# Amy 的印尼研究院

專為印尼市場情報設計的 Streamlit 新聞聚合與分析儀表板。

## ✨ 特色 (Features)

- **總體經濟 (Macro)**: 關注印尼政經局勢 (大選、新首都 Nusantara) 與台印關係最新動態。
- **產業趨勢 (Industry)**: 聚焦 **電動車 (EV)**、**電池**、**鎳礦** 與電子製造供應鏈。
- **重點台商 (VIP)**: 追蹤 10+ 家指標台廠（鴻海、和碩、台達電、Gogoro 等）在印尼的投資動態。
- **AI 賦能**: 自動生成 Prompt，協助您使用 ChatGPT 進行深度產業分析。
- **行動優化**: 手機版面自動適配，隨時掌握南向商機。

## 🛠️ 技術棧 (Tech Stack)

- **Python**
- **Streamlit**: Web 應用框架
- **Feedparser**: RSS 新聞爬蟲 (Google News)

## 🚀 快速開始 (Usage)

1. **安裝依賴**:
```bash
pip install -r requirements.txt
```

2. **啟動應用**:
```bash
streamlit run app.py
```

3. **操作指南**:
   - 左側選擇「時間範圍」與「主題」。
   - 程式會自動爬取新聞並生成 AI Prompt。
   - 複製 Prompt 貼給 ChatGPT，即可獲得專業分析報告。
