# 🛍 Divar Advanced Search Telegram Bot

A feature-rich Telegram bot that searches [Divar.ir](https://divar.ir) listings by keyword, city, and price range,
cleans and formats the results, and sends titles, prices, images, and direct links to your Telegram chat.

## 📖 Overview

This is a production-style Telegram bot that helps you find products on Divar quickly and efficiently.
Built in Python using `telebot` and `BeautifulSoup4`, it scrapes Divar pages, extracts product details,
and sends them as beautiful Telegram messages with inline images and clickable links.

## ✨ Key Features

- 🔍 **Advanced Search** — keyword, result count, city selection, and optional price range
- 🌆 **City Support** — major Iranian cities and an "all Iran" option
- 💰 **Price Filters** — set minimum/maximum prices in تومان
- 🖼 **Images & Links** — sends product images with clean captions and clickable links
- 🧹 **Clean Data Extraction** — product title, price, metadata, and image validation
- ⚡ **Responsive** — scraping runs in a background thread to avoid delays
- 🔄 **Fallback Selectors** — multiple HTML parsing methods to handle changes in Divar's layout
- 🛡 **Validation** — ignores irrelevant listings (services, repairs, etc.)

## 🛠 Tech Stack

- **Python 3**
- [pyTelegramBotAPI (telebot)](https://github.com/eternnoir/pyTelegramBotAPI)
- [Requests](https://docs.python-requests.org/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Regex](https://docs.python.org/3/library/re.html)
- `threading` for non-blocking scraping

## ⚙️ How It Works

1. Start the bot with `/start`
2. Enter **product name**
3. Choose **number of results** (5–30)
4. Select **city**
5. Optional: set **min/max price**
6. Get results with:
   - 🏷 Title
   - 💰 Price
   - 📍 Metadata (location, time, condition)
   - 🖼 Image
   - 🔗 Direct link

## 📦 Installation

```bash
# 1) Clone the repository
git clone https://github.com/AradRouhaniiiiii/Divar-Advanced-Search-Bot.git
cd Divar-Advanced-Search-Bot

# 2) Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3) Install dependencies
pip install -r requirements.txt
```

## 🔑 Configuration

1. Create a bot via [@BotFather](https://t.me/BotFather) and get your **API token**
2. Open `bot.py` and set:
   ```python
   BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
   ```

## 🚀 Run the Bot

```bash
python bot.py
```

Expected output:
```
🚀 Bot is running and ready to search Divar!
```

## 🖼 Example Interaction

```
/start
🛍️ جستوجوی محصول → "لپ تاپ ایسوس"
🔢 تعداد نتایج → 15
🏙️ شهر → تهران
💰 محدوده قیمت → از 20,000,000 تا 45,000,000
✅ ارسال نتایج با عکس + لینک
```

Example message:

```
📦 محصول 1:
🏷️ لپ تاپ ایسوس مدل X515
💰 15,000,000 تومان
📍 تهران | 2 ساعت پیش | نو

🔗 مشاهده آگهی: https://divar.ir/v/some-product-link
```

## ⚠️ Notes

- Respect [Divar’s Terms of Service](https://divar.ir/terms)
- Avoid sending too many requests in a short time
- HTML structure changes on Divar may require updates to selectors

## 📜 License

MIT License — use and modify freely, but please give credit.

## 🌍 Connect with Me
<p align="center">
  <a href="https://aradrouhani.com"><img src="https://img.shields.io/badge/Website-000000?logo=About.me&logoColor=white" /></a>
  <a href="https://www.instagram.com/AradRouhani_com"><img src="https://img.shields.io/badge/Instagram-%23E4405F.svg?logo=Instagram&logoColor=white" /></a>
  <a href="https://t.me/aradrouhani_com"><img src="https://img.shields.io/badge/Telegram-2CA5E0?logo=telegram&logoColor=white" /></a>
  <a href="https://www.kaggle.com/aradrouhani"><img src="https://img.shields.io/badge/Kaggle-20BEFF?logo=kaggle&logoColor=white" /></a>
  <a href="mailto:a.rouhaniiiiii@gmail.com"><img src="https://img.shields.io/badge/Email-D14836?logo=gmail&logoColor=white" /></a>
  <a href="https://github.com/AradRouhaniiiiii"><img src="https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white" /></a>
</p>
