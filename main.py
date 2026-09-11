import os
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
EBAY_CLIENT_ID = os.environ.get("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.environ.get("EBAY_CLIENT_SECRET")

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

def save_to_supabase(product_data):
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    res = requests.post(url, json=product_data, headers=headers)
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

            product_data = {
                "title": title,
                "ebay_price": price,
                "supplier_price": supplier_price,
                "profit": profit,
                "ebay_url": ebay_url,
                "daily_sales": 4,
                "weekly_sales": 25,
                "total_sales": 1050,
                "is_new_listing": False,
                "competitor_count": competitor_count,
                "best_market": best_market,
                "is_top_usa": market_stats.get("USA", {}).get("items_found", 0) > 0,
                "is_top_uk": market_stats.get("UK", {}).get("items_found", 0) > 0,
                "is_top_australia": market_stats.get("Australia", {}).get("items_found", 0) > 0,
                "is_top_canada": market_stats.get("Canada", {}).get("items_found", 0) > 0
            }

            if save_to_supabase(product_data):
                print(f"✅ Saved to Supabase: {title[:25]}...")
            else:
                print(f"❌ Failed to insert")

if __name__ == "__main__":
    fetch_and_save_winning_products("trending gadgets")
          
