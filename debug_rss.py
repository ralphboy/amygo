
import logic
import feedparser
import urllib.parse
import requests

def debug_rss():
    print("=== Debugging RSS Fetching (Extended) ===")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Test Case 1: English Only (No encoding issues expected)
    print("\n[Test 1: English 'Indonesia' with current logic]")
    url_en = f"https://news.google.com/rss/search?q={urllib.parse.quote_plus('Indonesia')}+when:3d&hl=en-ID&gl=ID&ceid=ID:en"
    try:
        r = requests.get(url_en, headers=headers, timeout=5)
        f = feedparser.parse(r.content)
        print(f"URL: {url_en}")
        print(f"Status: {r.status_code}, Entries: {len(f.entries)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test Case 2: Original Code Style (No manual quote_plus)
    print("\n[Test 2: Original Style '印尼' (Raw Unicode)]")
    # Original logic: f"https://news.google.com/rss/search?q=印尼+when:{days}d..."
    url_raw = "https://news.google.com/rss/search?q=印尼+when:3d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        # Note: requests.get(url) will auto-encode the URL
        r = requests.get(url_raw, headers=headers, timeout=5)
        f = feedparser.parse(r.content)
        print(f"URL: {url_raw}")
        print(f"Status: {r.status_code}, Entries: {len(f.entries)}")
    except Exception as e:
         print(f"Error: {e}")

    # Test Case 3: Current Code Style (Manual quote_plus)
    print("\n[Test 3: Current Style '印尼' (Manual component encoding)]")
    url_manual = f"https://news.google.com/rss/search?q={urllib.parse.quote_plus('印尼')}+when:3d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        r = requests.get(url_manual, headers=headers, timeout=5)
        f = feedparser.parse(r.content)
        print(f"URL: {url_manual}")
        print(f"Status: {r.status_code}, Entries: {len(f.entries)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test Case 4: Fully Encoded URL (Whole query encoded? No, Google RSS expects q=...&hl=...)
    # Test alternative encoding for space: %20 instead of +
    print("\n[Test 4: Space as %20]")
    url_space = f"https://news.google.com/rss/search?q={urllib.parse.quote_plus('印尼')}%20when:3d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        r = requests.get(url_space, headers=headers, timeout=5)
        f = feedparser.parse(r.content)
        print(f"URL: {url_space}")
        print(f"Status: {r.status_code}, Entries: {len(f.entries)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    debug_rss()
