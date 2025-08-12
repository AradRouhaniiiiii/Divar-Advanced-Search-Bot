🛍 Divar Advanced Search Telegram Bot

Search Divar.ir directly from Telegram with city, price, and keyword filters — get clean titles, prices, images, and direct links without the clutter.

Overview
--------
This is a production-style Telegram bot that helps you find products on Divar quickly and efficiently.
Built in Python using telebot and BeautifulSoup4, it scrapes Divar pages, extracts product details, and sends them as beautiful Telegram messages with inline images and clickable links.

Key Features
------------
- Full search flow: product → count → city → (optional) price range
- City presets: Tehran, Mashhad, Isfahan, Shiraz, and more — plus "all Iran" option
- Price filters: set min/max price in تومان
- Clean product info: title, price, metadata (location, time, condition)
- Image validation: checks images before sending to avoid broken links
- Fallback selectors: robust scraping against HTML changes
- Threaded scraping: keeps the bot responsive while processing requests

Tech Stack
----------
- Python 3
- pyTelegramBotAPI (telebot)
- Requests
- BeautifulSoup4
- regex for parsing and filtering
- threading for async-like performance

How It Works
------------
1. User sends /start to begin.
2. Bot asks for product name.
3. User chooses number of results (5–30).
4. User selects city from quick or full list.
5. Optional: user sets min/max price.
6. Bot scrapes Divar, validates data, and sends clean messages with:
   - 🏷 Title
   - 💰 Price
   - 📍 Metadata
   - 🖼 Image
   - 🔗 Direct link

Setup & Run
-----------
1) Clone this repo:
   git clone https://github.com/YourUsername/divar-advanced-search-bot.git
   cd divar-advanced-search-bot

2) Create a virtual environment:
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate

3) Install dependencies:
   pip install -r requirements.txt

4) Set your Telegram Bot token:
   export TELEGRAM_BOT_API_TOKEN="123456:ABC..."   # Windows (Powershell):  $env:TELEGRAM_BOT_API_TOKEN="..."

5) Run the bot:
   python bot.py

Example Interaction
-------------------
/start
🛍️ جستوجوی محصول → "لپ تاپ ایسوس"
🔢 تعداد نتایج → 15
🏙️ شهر → تهران
💰 محدوده قیمت → از 20,000,000 تا 45,000,000
✅ ارسال نتایج با عکس + لینک

Example message:
📦 محصول 1:
🏷️ لپ تاپ ایسوس مدل X515
💰 15,000,000 تومان
📍 تهران | 2 ساعت پیش | نو
🔗 مشاهده آگهی: https://divar.ir/v/some-product-link

Notes
-----
- Respect Divar’s Terms of Service: https://divar.ir/terms
- Avoid sending too many requests in a short time.
- HTML structure changes on Divar may require updates to selectors.

License
-------
MIT License — use and modify freely, but please give credit.
