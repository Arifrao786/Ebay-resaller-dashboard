import os
import requests

# Supabase Credentials (Supports both local & GitHub Secrets)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://doqmnxccvnmvcpneeueu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRvcW1ueGNjdm5tdmNwbmVldWV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwNjI2NzUsImV4cCI6MjEwNDYzODY3NX0.gy5QA0xh_yx26AZ_0d7upHtjCClBvIv48brdRE8NMhY")

# eBay Production Credentials
EBAY_CLIENT_ID = os.environ.get("EBAY_CLIENT_ID", "Muhammed-eBayTrac-PRD-082b86fbd-822d99a3")
EBAY_CLIENT_SECRET = os.environ.get("EBAY_CLIENT_SECRET", "PRD-82b86fbdc679-46bb-4a29-a4b1-ca4b")

MARKETPLACES = {
    "USA": "EBAY_US",
    "UK": "EBAY_GB",
    "Australia": "EBAY_AU",
    "Canada": "EBAY_CA"
}

COUNTRY_EVENTS = {
    "USA": {"event": "Memorial Day / Summer Sales", "date": "2026-05-25"},
    "UK": {"event": "Spring Bank Holiday Deals", "date": "2026-05-31"},
    "Australia": {"event": "EOFY Sales", "date": "2026-06-30"},
    "Canada": {"event": "Canada Day Promotions", "date": "2026-07-01"}
}

# ZIK Analytics removed and all major eBay Sold History & Research Extensions added
HUNTING_EXTENSIONS = (
    "1. DSers AliExpress Dropship: https://chromewebstore.google.com/detail/dsers-aliexpress-dropshipp/mpnchgbjgaocpijgaedjbehfjiljfcjh | "
    "2. AliDropship Tool: https://chromewebstore.google.com/detail/alidropship/omnnpnepdkacbpklopofcphjejbeppbp | "
    "3. eBay Sold History & Price Tracker: https://chromewebstore.google.com/ | "
    "4. Chili Hunter eBay Product Research: https://chromewebstore.google.com/ | "
    "5. AutoDS Helper Dropshipping Finder: https://chromewebstore.google.com/ | "
    "6. DSM Tool eBay Assistant: https://chromewebstore.google.com/"
)

AI_SEO_TOOLS_LINK = "https://www.copy.ai or https://chatgpt.com (AI Product Title & Description SEO Generator)"

def get_ebay_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    try:
        response = requests.post(url, headers=headers, data=data, auth=(EBAY_CLIENT_ID.strip(), EBAY_CLIENT_SECRET.strip()))
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print("Token Response Error:", response.text)
    except Exception as e:
        print("Token Error:", e)
    return None

def analyze_market_competitors(token, search_keyword):
    market_stats = {}
    for market_name, market_id in MARKETPLACES.items():
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": market_id
        }
        endpoint = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={search_keyword}&limit=5"
        res = requests.get(endpoint, headers=headers)
        if res.status_code == 200:
            data = res.json()
            market_stats[market_name] = {
                "competitors": data.get("total", 0),
                "items_found": len(data.get("itemSummaries", []))
            }
        else:
            market_stats[market_name] = {"competitors": 0, "items_found": 0}
    return market_stats

def save_to_supabase(product_data):
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    res = requests.post(url, json=product_data, headers=headers)
    if res.status_code not in [200, 201]:
        print("Supabase Error details:", res.text)
    return res.status_code in [200, 201]

def fetch_and_save_winning_products(search_keyword="trending gadgets"):
    print(f"🔎 Fetching live market data for: {search_keyword}...")
    token = get_ebay_token()
    if not token:
        print("❌ Authentication failed.")
        return

    market_stats = analyze_market_competitors(token, search_keyword)
    best_market = max(market_stats, key=lambda m: market_stats[m]["competitors"])
    competitor_count = market_stats[best_market]["competitors"]
    
    market_event_info = COUNTRY_EVENTS.get(best_market, {"event": "General Shopping Season", "date": "2026-06-01"})

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACES.get(best_market, "EBAY_US")
    }
    endpoint = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={search_keyword}&limit=10"
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        items = response.json().get("itemSummaries", [])
        if not items:
            print("⚠️ No items returned from eBay API.")
            return
            
        print(f"📦 Found {len(items)} products. Saving to Supabase...")
        for item in items:
            title = item.get("title", "No Title")
            ebay_url = item.get("itemWebUrl", "https://www.ebay.com")
            price = float(item.get("price", {}).get("value", 0.0))
            
            seller_info = item.get("seller", {})
            trending_seller = seller_info.get("username", "Top Rated eBay Seller")
            seller_url = f"https://www.ebay.com/str/{trending_seller}" if trending_seller else ebay_url

            supplier_price = round(price * 0.6, 2)
            profit = round(price - supplier_price, 2)

            product_data = {
                "title": title,
                "ebay_price": price,
                "supplier_price": supplier_price,
                "profit": profit,
                "ebay_url":ebay_url,
                "competitor_count": competitor_count,
                "best_market": best_market,
                "upcoming_events": market_event_info["event"],
                "event_date": market_event_info["date"],
                "trending_seller": trending_seller,
                "seller_url": seller_url,
                "hunting_extensions": HUNTING_EXTENSIONS,
                "ai_seo_tool_link": AI_SEO_TOOLS_LINK,
                "product_tag": "🔥 Today's Top Product",
                "is_top_usa": market_stats.get("USA", {}).get("items_found", 0) > 0,
                "is_top_uk": market_stats.get("UK", {}).get("items_found", 0) > 0,
                "is_top_australia": market_stats.get("Australia", {}).get("items_found", 0) > 0,
                "is_top_canada": market_stats.get("Canada", {}).get("items_found", 0) > 0
            }

            if save_to_supabase(product_data):
                print(f"✅ Saved: {title[:22]}... | Tag: 🔥 Today's Top Product")
            else:
                print(f"❌ Failed insert.")
    else:
        print("Fetch Error:", response.text)

if __name__ == "__main__":
    fetch_and_save_winning_products("trending gadgets")
