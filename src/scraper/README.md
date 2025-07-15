# TicketSwap Scraper

## Why
Regular web scraping fails due to TicketSwap's anti-bot protection. Google Apps Script with IMPORTXML bypasses this by using Google's infrastructure, which is typically whitelisted.

## How
1. Open Google Sheets
2. Go to Extensions > Apps Script
3. Paste `google-apps-script.js` code
4. Run `scrapeTicketSwapData()` function

## What it does
- Extracts: Available tickets, Sold tickets, Wanted tickets
- Adds timestamped row to your sheet
- Works reliably without rate limiting

## What's missing
- **Ticket prices** - These are loaded via JavaScript after page load, IMPORTXML can't capture them
- **Real-time updates** - Manual execution only (could add triggers)
- **Multiple events** - Hardcoded for Lowlands 2025

## Output columns
`Timestamp | Available | Sold | Wanted | Status`
