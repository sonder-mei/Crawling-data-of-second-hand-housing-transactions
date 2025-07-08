# Functionality
This tool enables multi-region crawling of transaction and listing data for second-hand houses in target cities on BeiKe.

  - `BeiKe_deal.py`: Code for crawling transaction data.
  - `BeiKe_salling.py`: Code for crawling listing data.

## Usage
1. Modify the user configuration area:
   - Replace `cookies` with your own account cookies after logging into the platform
     (F12 → "Application" → "Cookies")
   - Change `REGIONS/region` to target regions
   - Keep other settings unchanged

## Example Configuration
```python
# ================== User Configuration Area ==================
CONFIG = {
    "city": "sx",       # Target city in pinyin
    "cookies": {
        'lianjia_uuid': 'a9ba1fe8-770c-433e-a306-e8c30fbdab07',
        'lianjia_token': '2.00101efd5470ebd13a01b3d465afde00e5',
        'security_ticket': 'mrYyisn39oNOhtva8rHZtgjAmzD2t0jZa2iooYSnTZcp/GG7AdZJ/eidum6paOOw94UQLs3NjheXFWXyPMm7MhsKM+Exfrr9634s8A/RPBNWksBSAptLvY3jVLEbCj1SM8WvBM5ATgITRPRfD+1BkTpU27lrBDDZ/22CmOXcX8Q='
    },
    "srcid": 'eyJ0Ijoie1wiZGF0YVwiOlwiYWM3ZDhiNzA4ZGZjZjBlMzM1YzFhOWJmMmZiMDFlZGI5NGNkMGM4Yzg1NDIwZjg2OWQzMjA4NzBlODhhNmJiNjJmMDBmNTY4YTYyMDQzMDI5YjEyNjM5YzE2N2E4OTEyMDliMWZjZTgwYWYxYmZhOTMxMzU0MzQ4NWY1NDE1ODRkMDdiOWU2ZDYxZjdhMDgyZWY2ZmQ2YzgyN2UzMjIzNGJmNjZjYTAxZjQ2M2EzNzg0N2Q0MTgwY2Q2YzlkMTQ0MzUyNzdhYTliYmJjNWViMTJiOGE2MWJhNjZlZGVmMzY2OWVkMjUyNTVjMjU3OWQ3YzBjMjdlMjU0NzNiYmM2ZGQzMjEzMjA0ODJmNTdjNGYzNDc0MDBlODY5ZDRhMzA4MTFkN2NmN2Y3NWM3Y2RkZTI0YWJjMGM1NjRhY2Y2NmRcIixcImtleV9pZFwiOlwiMVwiLFwic2lnblwiOlwiZDlmMGFmMTJcIn0iLCJyIjoiaHR0cHM6Ly9zeC5rZS5jb20vY2hlbmdqaWFvLyIsIm9zIjoid2ViIiwidiI6IjAuMSJ9'
}

# Target regions to crawl
REGIONS = [ 
    "shangyuqu",
    "shengzhoushi",
    "xinchangxian",
    "zhujishi"
]
```
# Notes:
1. Data Preprocessing:
   - After crawling, simple data preprocessing is required using Excel

2. Cookies Instructions:
   - The current cookies can bypass some anti-scraping mechanisms  
   - **But please note:**
     - With large data volumes, the platform may still detect scraping activity
     - You may need to wait for account unblocking or use new cookies
