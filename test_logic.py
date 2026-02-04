
import logic
import urllib.parse

def test_url_encoding():
    print("Testing URL encoding...")
    # Test custom keyword with special handling
    sources = logic.get_rss_sources(3, "custom", "C&C++")
    url = sources[0]['url']
    print(f"URL for 'C&C++': {url}")
    if "C%26C%2B%2B" in url or "C%26C%2B%2B" in url.upper():
         print("PASS: Special characters encoded correctly.")
    else:
         print("FAIL: Special characters not encoded correctly.")

    # Test exact match quotes
    sources = logic.get_rss_sources(3, "vip")
    # Check one of the URLs
    url = sources[0]['url']
    print(f"VIP URL: {url}")
    # VIP_COMPANIES_CN has '"鴻海"'. quote_plus('"鴻海"') -> '%22%E9%B4%BB%E6%B5%B7%22'
    # VIP_QUERY_CN joins them.
    # We expect some encoded quotes.
    if "%22" in url:
        print("PASS: Quotes encoded correctly.")
    else:
        print("FAIL: Quotes not encoded.")

if __name__ == "__main__":
    try:
        test_url_encoding()
        print("Logic module imported and tested successfully.")
    except Exception as e:
        print(f"Error: {e}")
