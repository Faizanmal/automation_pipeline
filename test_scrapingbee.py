#!/usr/bin/env python
"""Test ScrapingBee API key and connectivity."""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")

if not SCRAPINGBEE_API_KEY:
    print("❌ SCRAPINGBEE_API_KEY not found in .env")
    exit(1)

print(f"🔑 Using ScrapingBee key: {SCRAPINGBEE_API_KEY[:20]}...")

try:
    r = httpx.post(
        'https://app.scrapingbee.com/api/v1/', 
        params={
            'api_key': SCRAPINGBEE_API_KEY, 
            'url': 'https://www.ubs.com', 
            'render_js': 'false'
        },
        timeout=30
    )
    print(f"✅ Status: {r.status_code}")
    print(f"📋 Response:\n{r.text[:1000]}")
except Exception as e:
    print(f"❌ Error: {e}")
