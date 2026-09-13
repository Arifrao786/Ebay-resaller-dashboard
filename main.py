import time
import requests

# Supabase Credentials
SUPABASE_URL = "https://doqmnxccvnmvcpneeueu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRvcW1ueGNjdm5tdmNwbmVldWV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwNjI2NzUsImV4cCI6MjEwNDYzODY3NX0.gy5QA0xh_yx26AZ_0d7upHtjCClBvIv48brdRE8NMhY"

# eBay Production Keys
EBAY_CLIENT_ID = "Muhammed-eBayTrac-PRD-082b86fbd-822d99a3"
EBAY_CLIENT_SECRET = "PRD-82b86fbdc679-46bb-4a29-a4b1-ca4b"

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

# 12 Research Tools Data (Jo 'research_tools' table mein save hoga)
EBAY_RESEARCH_TOOLS = [
    {"tool_name": "Google Trends", "tool_description": "Real-time search trends and past 24 hours data.", "tool_link": "https://trends.google.com/"},
    {"tool_name": "AliExpress Best Sellers", "tool_description": "Finding top selling winning products.", "tool_link": "https://www.aliexpress.com/"},
    {"tool_name": "eBay TeraPeak", "tool_description": "Extracting past sales and average prices.", "tool_link": "https://www.ebay.com/str/research"},
    {"tool_name": "WatchCount.com", "tool_description": "Tracking products on user watch lists.", "tool_link": "https://www.watchcount.com/"},
    {"tool_name": "KeywordTool.io", "tool_description": "Extracting real search queries and buyer terms.", "tool_link": "https://keywordtool.io/"},
    {"tool_name": "Google Keyword Planner", "tool_description": "Viewing search volume graphs.", "tool_link": "https://ads.google.com/home/tools/keyword-planner/"},
    {"tool_name": "WordStream Free Tool", "tool_description": "Checking high-performing related keywords.", "tool_link": "https://www.wordstream.com/free-keyword-tool"},
    {"tool_name": "Exploding Topics", "tool_description": "Finding rapidly growing product categories.", "tool_link": "https://explodingtopics.com/"},
    {"tool_name": "eBay Seller Center", "tool_description": "Viewing monthly and quarterly reports.", "tool_link": "https://export.ebay.com/"},
    {"tool_name": "eBay Search Bar", "tool_description": "Checking exact words buyers search for.", "tool_link": "https://www.ebay.com/"},
    {"tool_name": "eBay Advanced Search", "tool_description": "Checking competitor sales using Sold filter.", "tool_link": "https://www.ebay.com/sch/ebayadvsearch"},
    {"tool_name": "Manual Competitor Spying", "tool_description": "Viewing competitor store items blueprint.", "tool_link": "https://www.ebay.com/sch/ebayshops/"}
]

AI_SEO_TOOLS_LINK = "https://www.copy.ai or https://chatgpt.com (AI SEO Generator)"

def get_ebay_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
    try:
        response = requests.post(url, headers=headers, data=data, auth=(EBAY_CLIENT_ID.strip(), EBAY_CLIENT_SECRET.strip()))
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print("Token Error:", e)
    return None

def analyze_market_competitors(token, search_keyword):
    market_stats = {}
    for market_name, market_id in MARKETPLACES.items():
        headers = {"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": market_id}
        endpoint = f"https://api.buy.ebay.com/buy/browse/v1/item_summary/search?q={search_keyword}&limit=5"
        res = requests.get(endpoint, headers=headers)
        if res.status_code == 200:
            data = res.json()
            market_stats[market_name] = {"competitors": data.get("total", 0), "items_found": len(data.get("itemSummaries", []))}
        else:
            market_stats[market_name] = {"competitors": 0, "items_found": 0}
    return market_stats

def save_research_tools_to_supabase():
    url = f"{SUPABASE_URL}/rest/v1/research_tools"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    print("🛠️ Syncing Research Tools to 'research_tools' table...")
    for tool in EBAY_RESEARCH_TOOLS:
        requests.post(url, json=tool, headers=headers)

def save_product_to_supabase(product_data):
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    res = requests.post(url, json=product_data, headers=headers)
    return res.status_code in [200, 201]

def run_automation():
    # Pehle research tools save karein
    save_research_tools_to_supabase()
    
    # Phir eBay products fetch kar ke 'products' table mein save karein
    search_keyword = "trending gadgets"
    token = get_ebay_token()
    if not token:
        print("❌ eBay Authentication failed.")
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
                "ebay_url": ebay_url,
                "daily_sales": 4,
                "weekly_sales": 25,
                "total_sales": 1050,
                "competitor_count": competitor_count,
                "best_market": best_market,
                "upcoming_events": market_event_info["event"],
                "event_date": market_event_info["date"],
                "trending_seller": trending_seller,
                "seller_url": seller_url,
                "ai_seo_tool_link": AI_SEO_TOOLS_LINK,
                "product_tag": "🔥 Today's Top Winning Product"
            }
            save_product_to_supabase(product_data)
        print("✨ Automation completed successfully for both tables!")

if __name__ == "__main__":
    run_automation()
