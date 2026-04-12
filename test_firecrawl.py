#!/usr/bin/env python
"""Test Firecrawl API key and connectivity."""

import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v0/scrape"

if not FIRECRAWL_API_KEY:
    print("❌ FIRECRAWL_API_KEY not found in .env")
    sys.exit(1)

print(f"🔑 Using Firecrawl key: {FIRECRAWL_API_KEY[:20]}...")

# Test simple request
payload = {
    "url": "https://www.ubs.com",
    "formats": ["markdown"],
}

headers = {
    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
}

print(f"📡 Testing Firecrawl API at {FIRECRAWL_API_URL}...")
print(f"📝 Payload: {payload}")

try:
    response = httpx.post(FIRECRAWL_API_URL, json=payload, headers=headers, timeout=30)
    print(f"✅ Status: {response.status_code}")
    print(f"📋 Response: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✅ Firecrawl API is working!")
        else:
            print(f"⚠️ API error: {data}")
    else:
        print(f"❌ API error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Request failed: {e}")
    sys.exit(1)
