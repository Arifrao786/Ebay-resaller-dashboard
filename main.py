import requests
from datetime import datetime

# Supabase Credentials
SUPABASE_URL = "https://doqmnxccvnmvcpneeueu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRvcW1ueGNjdm5tdmNwbmVldWV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkwNjI2NzUsImV4cCI6MjEwNDYzODY3NX0.gy5QA0xh_yx26AZ_0d7upHtjCClBvIv48brdRE8NMhY"

# eBay Production Credentials (Directly Added)
EBAY_CLIENT_ID = "Muhammed-eBayTrac-PRD-082b86fbd-822d99a3"
EBAY_CLIENT_SECRET = "PRD-82b86fbdc679-46bb-4a29-a4b1-ca4b"

MARKETPLACES = {
    "USA": "EBAY_US",
    "UK": "EBAY_GB",
    "Australia": "EBAY_AU",
    "Canada": "EBAY_CA"
}

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
        endpoint = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={search_keyword}&limit=10"
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

def save_to_supabase(table_name, data_payload):
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    res = requests.post(url, json=data_payload, headers=headers)
    if res.status_code not in [200, 201]:
        print(f"Supabase Error ({table_name}):", res.text)
    return res.status_code in [200, 201]

def seed_research_tools():
    print("🛠️ Seeding research tools into Supabase...")
    tools = [
        {
            "tool_name": "eBay Product Research (Terapeak)",
            "tool_description": "Official eBay tool for market trends and sales history.",
            "tool_link": "https://www.ebay.com/sh/research"
        },
        {
            "tool_name": "AliExpress Dropshipping Center",
            "tool_description": "Find winning products and analyze supplier pricing.",
            "tool_link": "https://www.aliexpress.com"
        },
        {
            "tool_name": "ChatGPT AI Optimizer",
            "tool_description": "Generate high-converting eBay titles and descriptions.",
            "tool_link": "https://chatgpt.com"
        }
    ]
    for tool in tools:
        save_to_supabase("research_tools", tool)

def fetch_and_save_winning_products(search_keyword="trending gadgets"):
    print(f"🔎 Fetching live market data for: {search_keyword}...")
    token = get_ebay_token()
    if not token:
        print("❌ Authentication failed. Check Client ID & Secret.")
        return
    
    # Pehle research tools seed kardein
    seed_research_tools()

    market_stats = analyze_market_competitors(token, search_keyword)
    best_market = max(market_stats, key=lambda m: market_stats[m]["competitors"])
    competitor_count = market_stats[best_market]["competitors"]

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
            
            supplier_price = round(price * 0.6, 2)
            profit = round(price - supplier_price, 2)

            # Naye columns ka data jo aapnedashboard ke liye manga hai
            product_data = {
                "title": title,
                "ebay_price": price,
                "supplier_price": supplier_price,
                "profit": profit,
                "ebay_url": ebay_url,
                "daily_sales": "25 sold",
                "weekly_sales": "210 sold",
                "total_sales": "950 sold",
                "is_new_listing": False,
                "competitor_count": competitor_count,
                "best_market": best_market,
                "market": best_market,
                "is_top_usa": market_stats.get("USA", {}).get("items_found", 0) > 0,
                "is_top_uk": market_stats.get("UK", {}).get("items_found", 0) > 0,
                "is_top_australia": market_stats.get("Australia", {}).get("items_found", 0) > 0,
                "is_top_canada": market_stats.get("Canada", {}).get("items_found", 0) > 0,
                # New Columns Added Here:
                "trending_seller": "Top_Seller_99",
                "seller_url": "https://www.ebay.com/str/topseller",
                "hunting_extensions": "Hunter Extension v2",
                "ai_seo_tool_link": "https://chatgpt.com",
                "upcoming_event": "Market Resell Spike",
                "event_date": datetime.now().strftime("%Y-%m-%d")
            }

            if save_to_supabase("products", product_data):
                print(f"✅ Saved to Supabase: {title[:25]}... | Market: {best_market}")
            else:
                print(f"❌ Failed to insert: {title[:20]}")
    else:
        print("Fetch Error:", response.text)

if __name__ == "__main__":
    fetch_and_save_winning_products("trending gadgets")
