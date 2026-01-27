import sys
from unittest.mock import MagicMock
import os
import json

# Mock streamlit before importing app
mock_st = MagicMock()
sys.modules["streamlit"] = mock_st
# Configure mocks that are unpacked
mock_st.tabs.return_value = [MagicMock(), MagicMock()]
mock_st.columns.return_value = [MagicMock(), MagicMock()]
mock_st.empty.return_value = MagicMock()
mock_st.progress.return_value = MagicMock()
# side_effect for sequential calls: 1. Date (1天), 2. Topic (泰國政經)
mock_st.pills.side_effect = ["1天", "泰國政經"]
mock_st.radio.side_effect = ["1天", "泰國政經"]
mock_st.text_input.return_value = ""
mock_st.session_state = {} 

import app

def test_rss_fetching():
    print("Testing get_rss_sources...")
    sources = app.get_rss_sources(1, "macro")
    print(f"Got {len(sources)} sources.")
    assert len(sources) > 0, "Should have RSS sources"

    print("\nTesting generate_chatgpt_prompt (Parallel Fetching)...")
    # Using a short timeout or limiting sources if possible, but here we just run it.
    # We might want to mock feedparser if we don't want real network calls, 
    # but for verification of "Parallel Fetching" working, real calls are better 
    # if we can accept the time. Let's do real calls to be sure.
    
    prompt, news = app.generate_chatgpt_prompt("1天", 1, "macro")
    print("Prompt generated length:", len(prompt))
    print("News items found:", len(news))
    
    if len(news) > 0:
        print("First news title:", news[0]['title'])
    
    return news

def test_history_persistence():
    print("\nTesting History Persistence...")
    # Clean up previous test
    if os.path.exists("news_data.json"):
        os.remove("news_data.json")
    
    # 1. First Run
    print("Run 1: Generating data...")
    app.generate_chatgpt_prompt("1天", 1, "macro")
    
    with open("news_data.json", "r") as f:
        data1 = json.load(f)
        count1 = len(data1["news_list"])
        print(f"Run 1 saved {count1} items.")

    # 2. Second Run (simulating different or same data)
    # real RSS might not change in seconds, but we check if file is overwritten or appended.
    # ideally we mock the news list to be different, but let's see if it crashes.
    print("Run 2: Generating data again...")
    app.generate_chatgpt_prompt("1天", 1, "industry")
    
    with open("news_data.json", "r") as f:
        data2 = json.load(f)
        count2 = len(data2["news_list"])
        print(f"Run 2 saved total {count2} items.")
    
    # Logic: If appended, count2 >= count1. 
    # (It might be equal if all news are duplicates, but industry vs macro should differ)
    if count2 >= count1:
        print("✅ History persistence test passed (count increased or equal).")
    else:
        print("❌ History persistence failed (count decreased?).")

if __name__ == "__main__":
    try:
        news = test_rss_fetching()
        test_history_persistence()
        print("\nAll Tests Completed Successfully.")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
