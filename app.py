# ================= 網頁主程式 (修正版) =================

st.markdown('<div class="big-font">ThaiNews.Ai 🇹🇭 戰情室</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🤖 生成器", "📊 歷史庫"])

with tab1:
    c_left, c_right = st.columns([1, 3], gap="medium")
    
    with c_left:
        st.markdown('<h5 class="mobile-hidden">⚙️ 設定操作</h5>', unsafe_allow_html=True)
        
        # [狀態管理] 完整初始化
        if 'days_int' not in st.session_state: 
            st.session_state['days_int'] = 1
        if 'search_type' not in st.session_state: 
            st.session_state['search_type'] = None
        if 'search_keyword' not in st.session_state: 
            st.session_state['search_keyword'] = ""
        if 'pills_date' not in st.session_state: 
            st.session_state['pills_date'] = "1天"
        if 'pills_topic' not in st.session_state: 
            st.session_state['pills_topic'] = None  # 新增初始化
        if 'last_search_config' not in st.session_state:
            st.session_state['last_search_config'] = None  # 紀錄上次搜尋配置

        # 1. 時間選擇
        st.markdown('<div class="caption-text mobile-hidden" style="font-size:0.8em; color:gray; margin-bottom:4px;">1. 時間範圍</div>', unsafe_allow_html=True)
        date_selection = st.pills(
            "Time", 
            list(DATE_MAP.keys()), 
            default=st.session_state['pills_date'],
            label_visibility="collapsed", 
            key="pills_date_widget"
        )
        
        if date_selection:
            st.session_state['days_int'] = DATE_MAP[date_selection]
            st.session_state['pills_date'] = date_selection

        # 2. 主題選擇
        st.markdown('<div class="caption-text mobile-hidden" style="font-size:0.8em; color:gray; margin-bottom:4px;">2. 分析主題</div>', unsafe_allow_html=True)
        
        topic_selection = st.pills(
            "Topic", 
            list(TOPIC_MAP.keys()), 
            default=st.session_state.get('pills_topic'),
            label_visibility="collapsed", 
            selection_mode="single", 
            key="pills_topic_widget"
        )
        
        # 當主題選擇改變時，設定搜尋模式
        if topic_selection:
            target_mode = TOPIC_MAP[topic_selection]
            st.session_state['search_type'] = target_mode
            st.session_state['search_keyword'] = ""  # 清空關鍵字
            st.session_state['pills_topic'] = topic_selection

        # 3. 自訂搜尋
        st.markdown('<div class="caption-text mobile-hidden" style="font-size:0.8em; color:gray; margin-bottom:4px;">3. 關鍵字</div>', unsafe_allow_html=True)
        
        c_in, c_btn = st.columns([3, 1], gap="small")
        
        with c_in:
            custom_kw = st.text_input(
                "Keywords", 
                placeholder="輸入關鍵字 (如: Delta)", 
                key="kw_input", 
                label_visibility="collapsed"
            )
        
        with c_btn:
            if st.button("🔍", type="primary", use_container_width=True):
                if custom_kw.strip():
                    st.session_state['search_type'] = "custom"
                    st.session_state['search_keyword'] = custom_kw.strip()
                    st.session_state['pills_topic'] = None  # 清除主題選擇
                    st.rerun()

    # 右側：顯示結果區域
    with c_right:
        days_int = st.session_state['days_int']
        selected_label = st.session_state['pills_date']
        
        s_type = st.session_state.get('search_type')
        s_kw = st.session_state.get('search_keyword', "")
        
        # 建立當前搜尋配置的唯一識別
        current_config = f"{s_type}_{s_kw}_{days_int}"
        last_config = st.session_state.get('last_search_config')
        
        # 判斷是否需要執行新搜尋
        should_search = (s_type is not None) and (current_config != last_config)
        
        # 尚未搜尋時的歡迎畫面
        if not s_type:
            st.markdown("""
            #### 歡迎來到 ThaiNews.Ai 🇹🇭
            * **泰國政經情勢**：涵蓋泰國政經、政策與台泰關係。
            * **電子產業趨勢**：專注 PCB、伺服器與電子製造供應鏈。
            * **重點台商動態**：鎖定 10 大重點台商 (鴻海、台達電、廣達等) 動態。
            
            👈 請從左側選擇主題或輸入關鍵字開始搜尋
            """)
        
        # 執行搜尋
        elif should_search:
            # 更新配置記錄
            st.session_state['last_search_config'] = current_config
            
            if s_type == "custom" and s_kw:
                with st.spinner(f"正在全網搜索「{s_kw}」..."):
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
        
        # 已有搜尋結果但未改變配置（顯示提示）
        elif s_type and not should_search:
            st.info("💡 搜尋結果已載入。修改時間範圍或選擇其他主題以更新結果。")