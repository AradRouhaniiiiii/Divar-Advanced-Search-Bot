import telebot
import threading
import logging
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "TELEGRAM_BOT_API_TOKEN"
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# Iranian cities data for Divar
CITIES_DATA = {
    "iran": "همه ایران",
    "tehran": "تهران", 
    "mashhad": "مشهد",
    "isfahan": "اصفهان",
    "karaj": "کرج",
    "tabriz": "تبریز",
    "shiraz": "شیراز",
    "ahvaz": "اهواز",
    "qom": "قم",
    "kermanshah": "کرمانشاه",
    "urmia": "ارومیه",
    "rasht": "رشت",
    "zahedan": "زاهدان",
    "hamadan": "همدان",
    "kerman": "کرمان",
    "yazd": "یزد",
    "ardabil": "اردبیل",
    "bandar-abbas": "بندرعباس",
    "eslamshahr": "اسلامشهر",
    "zanjan": "زنجان",
    "sanandaj": "سنندج",
    "qazvin": "قزوین",
    "khorramabad": "خرم‌آباد",
    "gorgan": "گرگان",
    "sari": "ساری",
    "dezful": "دزفول",
    "bushehr": "بوشهر",
    "qods": "قدس",
    "varamin": "ورامین",
    "malard": "ملارد",
    "borujerd": "بروجرد",
    "abadan": "آبادان",
    "najafabad": "نجف‌آباد",
    "khorramshahr": "خرمشهر",
    "rey": "ری",
    "shahr-e-kord": "شهرکرد",
    "ilam": "ایلام",
    "birjand": "بیرجند",
    "semnan": "سمنان",
    "amol": "آمل",
    "bojnurd": "بجنورد",
    "yasuj": "یاسوج"
}

def scrape_divar_products(query: str, max_items: int, city: str = "tehran", min_price: int = None, max_price: int = None):
    """Improved scraper for Divar products with clean data extraction"""
    try:
        # Build URL with filters
        base_url = f"https://divar.ir/s/{city}"
        params = {"q": query}
        
        if min_price is not None or max_price is not None:
            price_filter = ""
            if min_price is not None:
                price_filter += f"MIN-{min_price}"
            if max_price is not None:
                if price_filter:
                    price_filter += f"_MAX-{max_price}"
                else:
                    price_filter += f"MAX-{max_price}"
            if price_filter:
                params["price"] = price_filter

        # Create URL with parameters
        url = base_url + "?" + "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fa,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Try multiple approaches to find products
        results = []
        
        # Method 1: Look for product links with specific patterns
        product_links = soup.find_all('a', href=re.compile(r'/v/[^/]+'))
        
        for link in product_links[:max_items * 2]:  # Get more to filter later
            try:
                product = extract_product_from_link(link)
                if product and is_valid_product(product):
                    results.append(product)
                    if len(results) >= max_items:
                        break
            except Exception as e:
                logger.error(f"Error extracting product from link: {e}")
                continue
        
        # Method 2: If no results, try alternative selectors
        if not results:
            logger.info("Trying alternative extraction method...")
            containers = soup.find_all(['article', 'div'], attrs={'class': re.compile(r'post|item|card')})
            
            for container in containers[:max_items * 2]:
                try:
                    product = extract_product_from_container(container)
                    if product and is_valid_product(product):
                        results.append(product)
                        if len(results) >= max_items:
                            break
                except Exception as e:
                    continue
        
        return results[:max_items]
    
    except Exception as e:
        logger.error(f"Error scraping Divar: {e}")
        return []

def extract_product_from_container(container):
    """Alternative method to extract product info from any container"""
    product = {}
    
    try:
        # Find any link inside container
        link = container.find('a', href=re.compile(r'/v/'))
        if link:
            href = link.get('href')
            product['url'] = f"https://divar.ir{href}" if href.startswith('/') else href
        
        # Extract title from multiple possible elements
        title_candidates = container.find_all(['h1', 'h2', 'h3', 'h4', 'span', 'div'])
        title = None
        
        for candidate in title_candidates:
            text = candidate.get_text(strip=True)
            if text and 5 <= len(text) <= 200 and not any(x in text.lower() for x in ['تومان', 'ساعت', 'دقیقه']):
                title = text
                break
        
        if not title:
            return None
        
        product['title'] = re.sub(r'\s+', ' ', title)
        
        # Extract price
        price_elements = container.find_all(string=re.compile(r'تومان'))
        price = "قیمت نامشخص"
        
        for price_elem in price_elements:
            if price_elem and isinstance(price_elem, str):
                price_text = price_elem.strip()
                if 'تومان' in price_text and len(price_text) < 100:
                    price = re.sub(r'\s+', ' ', price_text)
                    break
        
        product['price'] = price
        
        # Extract image with better validation
        img_element = container.find('img')
        if img_element:
            img_candidates = [
                img_element.get('src'),
                img_element.get('data-src'),
                img_element.get('data-lazy-src'),
                img_element.get('srcset'),
                img_element.get('data-srcset')
            ]
            
            for candidate in img_candidates:
                if candidate and is_valid_image_url(candidate):
                    # Clean srcset if needed
                    if 'srcset' in str(candidate):
                        # Extract first URL from srcset
                        urls = re.findall(r'(https?://[^\s,]+)', candidate)
                        if urls:
                            candidate = urls[0]
                    
                    if candidate.startswith('//'):
                        candidate = 'https:' + candidate
                    elif candidate.startswith('/'):
                        candidate = 'https://divar.ir' + candidate
                    
                    cleaned_url = clean_image_url(candidate)
                    if cleaned_url:
                        product['image_url'] = cleaned_url
                        break
        
        # Extract meta information
        meta_info = []
        all_texts = container.find_all(string=True)
        
        for text in all_texts:
            text = text.strip()
            if text and 3 <= len(text) <= 30:
                if any(indicator in text for indicator in ['در ', 'ساعت', 'دقیقه', 'نو', 'کارکرده']):
                    if text not in meta_info:
                        meta_info.append(text)
                        if len(meta_info) >= 3:
                            break
        
        product['meta'] = " | ".join(meta_info) if meta_info else "اطلاعات کامل در لینک موجود است"
        
        return product
        
    except Exception as e:
        logger.error(f"Error in extract_product_from_container: {e}")
        return None

def extract_product_from_link(link_element):
    """Extract product information from a product link element"""
    product = {}
    
    try:
        # Extract URL
        href = link_element.get('href')
        if href:
            product['url'] = f"https://divar.ir{href}" if href.startswith('/') else href
        
        # Find the container that holds all product info
        container = link_element
        
        # Extract title - look for h2 or the main title element
        title_element = container.find('h2')
        if not title_element:
            title_element = container.find(['h1', 'h3', 'h4'])
        if not title_element:
            # Look for title in nested divs
            title_element = container.find('div', string=True)
        
        if title_element:
            title = title_element.get_text(strip=True)
            # Clean title from extra characters
            title = re.sub(r'\s+', ' ', title)
            product['title'] = title
        else:
            return None
        
        # Extract price - look for elements containing "تومان"
        price_elements = container.find_all(string=re.compile(r'تومان'))
        price = "قیمت نامشخص"
        
        for price_elem in price_elements:
            price_text = price_elem.strip()
            if price_text and 'تومان' in price_text:
                # Clean and format price
                price = re.sub(r'\s+', ' ', price_text)
                break
        
        product['price'] = price
        
        # Extract image
        img_element = container.find('img')
        if img_element:
            img_src = img_element.get('src') or img_element.get('data-src') or img_element.get('data-lazy-src')
            if img_src and is_valid_image_url(img_src):
                # Make sure URL is complete and clean
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = 'https://divar.ir' + img_src
                
                # Clean URL from invalid characters
                img_src = clean_image_url(img_src)
                if img_src:
                    product['image_url'] = img_src
        
        # Extract metadata (location, time, etc.)
        meta_info = []
        
        # Look for location and time info
        text_elements = container.find_all(string=True)
        for text in text_elements:
            text = text.strip()
            if text and len(text) > 2:
                # Check if it's location info (contains "در")
                if 'در ' in text and len(text) < 50:
                    meta_info.append(text)
                # Check if it's time info (contains time indicators)
                elif any(word in text for word in ['ساعت', 'دقیقه', 'روز', 'هفته', 'ماه']) and len(text) < 30:
                    meta_info.append(text)
                # Check if it's condition info
                elif any(word in text for word in ['نو', 'کارکرده', 'سالم', 'معاوضه']) and len(text) < 20:
                    meta_info.append(text)
        
        # Remove duplicates and join
        meta_info = list(dict.fromkeys(meta_info))  # Remove duplicates while preserving order
        product['meta'] = " | ".join(meta_info[:3]) if meta_info else "اطلاعات کامل در لینک موجود است"
        
        return product
        
    except Exception as e:
        logger.error(f"Error in extract_product_from_link: {e}")
        return None

def is_valid_image_url(url):
    """Check if the image URL is valid for Telegram"""
    if not url:
        return False
    
    # Check for valid image extensions
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    url_lower = url.lower()
    
    # Check if URL contains valid image indicators
    if any(ext in url_lower for ext in valid_extensions):
        return True
    
    # Check for common image hosting patterns
    image_patterns = ['cdn', 'img', 'image', 'static', 'media']
    if any(pattern in url_lower for pattern in image_patterns):
        return True
    
    return False

def clean_image_url(url):
    """Clean and validate image URL for Telegram"""
    if not url:
        return None
    
    try:
        # Remove invalid characters that Telegram doesn't accept
        import urllib.parse
        
        # Parse URL to check if it's valid
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            return None
        
        # Reconstruct clean URL
        clean_url = urllib.parse.urlunparse(parsed)
        
        # Additional validation
        if len(clean_url) > 2048:  # Telegram URL limit
            return None
        
        # Check for suspicious patterns
        suspicious = ['javascript:', 'data:', 'blob:', 'file:']
        if any(pattern in clean_url.lower() for pattern in suspicious):
            return None
        
        return clean_url
    
    except Exception:
        return None

def is_valid_product(product):
    """Check if extracted product data is valid"""
    if not product.get('title'):
        return False
    
    title = product['title'].lower()
    
    # Filter out service ads
    invalid_keywords = [
        'تعمیرکار', 'تعمیرات', 'نصب', 'سرویس', 'خدمات', 
        'تعمیر', 'نگهداری', 'راه اندازی', 'پشتیبانی'
    ]
    
    for keyword in invalid_keywords:
        if keyword in title:
            return False
    
    # Check if title is too short or too long
    if len(product['title']) < 5 or len(product['title']) > 200:
        return False
    
    return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_states[user_id] = {}
    welcome_text = """🔍 سلام! به ربات جستجوی پیشرفته دیوار خوش آمدید

✨ امکانات جدید:
• جستجو در تمام شهرهای ایران
• فیلتر قیمت دقیق
• نمایش تصاویر محصولات
• اطلاعات کامل و تمیز

🚀 برای شروع روی دکمه زیر کلیک کنید!"""
    
    bot.send_message(message.chat.id, welcome_text)
    show_main_menu(message.chat.id)

def show_main_menu(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        telebot.types.InlineKeyboardButton("🛍️ جستوجوی محصول", callback_data="start_search"),
        telebot.types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help")
    )
    bot.send_message(chat_id, "چه کاری برایتان انجام دهم؟", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "start_search")
def start_search(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_states[user_id] = {"step": "waiting_product_name"}
    
    bot.send_message(chat_id, "📝 نام محصول مورد نظر خود را وارد کنید:\n\n💡 مثال: لپ تاپ ایسوس، گوشی سامسونگ، ماشین لباسشویی ال جی")

@bot.callback_query_handler(func=lambda call: call.data == "help")
def show_help(call):
    help_text = """📖 راهنمای کامل استفاده:

🔍 مراحل جستجو:
1️⃣ نام محصول را وارد کنید
2️⃣ تعداد نتایج را انتخاب کنید (5-30)
3️⃣ شهر مورد نظر را انتخاب کنید
4️⃣ اختیاری: محدوده قیمت تنظیم کنید
5️⃣ نتایج با تصویر دریافت کنید

✨ ویژگی‌های ویژه:
• اطلاعات تمیز و دقیق
• تصاویر با کیفیت
• لینک مستقیم به آگهی
• فیلتر پیشرفته قیمت
• پشتیبانی از تمام شهرها

🎯 نکات مهم:
• از کلمات کلیدی دقیق استفاده کنید
• برای نتایج بهتر نام برند را اضافه کنید
• محدوده قیمت واقعی وارد کنید"""
    
    bot.send_message(call.message.chat.id, help_text)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "waiting_product_name")
def handle_product_name(message):
    user_id = message.from_user.id
    product_name = message.text.strip()
    
    if not product_name or len(product_name) < 2:
        bot.send_message(message.chat.id, "❌ نام محصول باید حداقل 2 کاراکتر باشد. لطفاً دوباره وارد کنید:")
        return
    
    user_states[user_id]["product_name"] = product_name
    user_states[user_id]["step"] = "waiting_count"
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        telebot.types.InlineKeyboardButton("5️⃣", callback_data="count_5"),
        telebot.types.InlineKeyboardButton("🔟", callback_data="count_10"),
        telebot.types.InlineKeyboardButton("1️⃣5️⃣", callback_data="count_15"),
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("2️⃣0️⃣", callback_data="count_20"),
        telebot.types.InlineKeyboardButton("2️⃣5️⃣", callback_data="count_25"),
        telebot.types.InlineKeyboardButton("3️⃣0️⃣", callback_data="count_30")
    )
    
    bot.send_message(message.chat.id, f"✅ محصول: {product_name}\n\n🔢 چند نتیجه می‌خواهید؟", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("count_"))
def handle_count_selection(call):
    user_id = call.from_user.id
    count = int(call.data.split("_")[1])
    
    user_states[user_id]["count"] = count
    user_states[user_id]["step"] = "waiting_city"
    
    show_city_selection(call.message.chat.id)

def show_city_selection(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # Add major cities first
    major_cities = [
        ("iran", "🇮🇷 همه ایران"),
        ("tehran", "🏢 تهران"),
        ("mashhad", "🕌 مشهد"),
        ("isfahan", "🏛️ اصفهان"),
        ("karaj", "🏘️ کرج"),
        ("tabriz", "🏔️ تبریز"),
        ("shiraz", "🌹 شیراز"),
        ("ahvaz", "🏭 اهواز")
    ]
    
    for city_code, city_name in major_cities:
        keyboard.add(telebot.types.InlineKeyboardButton(city_name, callback_data=f"city_{city_code}"))
    
    keyboard.add(telebot.types.InlineKeyboardButton("📍 سایر شهرها...", callback_data="more_cities"))
    
    bot.send_message(chat_id, "🏙️ شهر مورد نظر خود را انتخاب کنید:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "more_cities")
def show_more_cities(call):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # Other cities
    other_cities = [
        ("qom", "قم"), ("kermanshah", "کرمانشاه"), ("urmia", "ارومیه"),
        ("rasht", "رشت"), ("zahedan", "زاهدان"), ("hamadan", "همدان"),
        ("kerman", "کرمان"), ("yazd", "یزد"), ("ardabil", "اردبیل"),
        ("bandar-abbas", "بندرعباس"), ("zanjan", "زنجان"), ("sanandaj", "سنندج"),
        ("qazvin", "قزوین"), ("gorgan", "گرگان"), ("sari", "ساری"),
        ("bushehr", "بوشهر"), ("dezful", "دزفول"), ("borujerd", "بروجرد")
    ]
    
    for city_code, city_name in other_cities:
        keyboard.add(telebot.types.InlineKeyboardButton(city_name, callback_data=f"city_{city_code}"))
    
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_major_cities"))
    
    bot.edit_message_text("🏙️ سایر شهرها:", call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_major_cities")
def back_to_major_cities(call):
    show_city_selection(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("city_"))
def handle_city_selection(call):
    user_id = call.from_user.id
    city_code = call.data.split("_")[1]
    city_name = CITIES_DATA.get(city_code, city_code)
    
    user_states[user_id]["city"] = city_code
    user_states[user_id]["step"] = "waiting_price_filter"
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        telebot.types.InlineKeyboardButton("💰 تنظیم محدوده قیمت", callback_data="set_price_filter"),
        telebot.types.InlineKeyboardButton("🚀 جستجو بدون فیلتر قیمت", callback_data="search_no_price_filter")
    )
    
    bot.send_message(call.message.chat.id, f"✅ شهر انتخاب شده: {city_name}\n\n💡 آیا می‌خواهید محدوده قیمت تنظیم کنید؟", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "set_price_filter")
def set_price_filter(call):
    user_id = call.from_user.id
    user_states[user_id]["step"] = "waiting_min_price"
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(telebot.types.InlineKeyboardButton("🚫 بدون حداقل قیمت", callback_data="skip_min_price"))
    
    bot.send_message(call.message.chat.id, "💰 حداقل قیمت را به تومان وارد کنید:\n\n💡 مثال: 1000000 (یک میلیون تومان)\n(یا روی دکمه زیر کلیک کنید)", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "skip_min_price")
def skip_min_price(call):
    user_id = call.from_user.id
    user_states[user_id]["min_price"] = None
    user_states[user_id]["step"] = "waiting_max_price"
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(telebot.types.InlineKeyboardButton("🚫 بدون حداکثر قیمت", callback_data="skip_max_price"))
    
    bot.send_message(call.message.chat.id, "💰 حداکثر قیمت را به تومان وارد کنید:\n\n💡 مثال: 5000000 (پنج میلیون تومان)\n(یا روی دکمه زیر کلیک کنید)", reply_markup=keyboard)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "waiting_min_price")
def handle_min_price(message):
    user_id = message.from_user.id
    
    try:
        min_price = int(message.text.strip().replace(',', '').replace('،', ''))
        if min_price < 0:
            raise ValueError("Negative price")
            
        user_states[user_id]["min_price"] = min_price
        user_states[user_id]["step"] = "waiting_max_price"
        
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(telebot.types.InlineKeyboardButton("🚫 بدون حداکثر قیمت", callback_data="skip_max_price"))
        
        bot.send_message(message.chat.id, f"✅ حداقل قیمت: {min_price:,} تومان\n\n💰 حداکثر قیمت را وارد کنید:", reply_markup=keyboard)
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید (فقط اعداد):")

@bot.callback_query_handler(func=lambda call: call.data == "skip_max_price")
def skip_max_price(call):
    user_id = call.from_user.id
    user_states[user_id]["max_price"] = None
    start_scraping(call.message.chat.id, user_id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "waiting_max_price")
def handle_max_price(message):
    user_id = message.from_user.id
    
    try:
        max_price = int(message.text.strip().replace(',', '').replace('،', ''))
        min_price = user_states[user_id].get("min_price")
        
        if max_price < 0:
            raise ValueError("Negative price")
        
        if min_price and max_price <= min_price:
            bot.send_message(message.chat.id, f"❌ حداکثر قیمت باید بیشتر از حداقل قیمت ({min_price:,} تومان) باشد:")
            return
            
        user_states[user_id]["max_price"] = max_price
        start_scraping(message.chat.id, user_id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید (فقط اعداد):")

@bot.callback_query_handler(func=lambda call: call.data == "search_no_price_filter")
def search_no_price_filter(call):
    user_id = call.from_user.id
    user_states[user_id]["min_price"] = None
    user_states[user_id]["max_price"] = None
    start_scraping(call.message.chat.id, user_id)

def start_scraping(chat_id, user_id):
    user_data = user_states.get(user_id, {})
    
    product_name = user_data.get("product_name")
    count = user_data.get("count")
    city = user_data.get("city")
    min_price = user_data.get("min_price")
    max_price = user_data.get("max_price")
    
    # Show search summary
    city_name = CITIES_DATA.get(city, city)
    summary = f"🔍 در حال جستجو...\n\n📦 محصول: {product_name}\n📊 تعداد: {count}\n🏙️ شهر: {city_name}"
    
    if min_price or max_price:
        price_range = "💰 محدوده قیمت: "
        if min_price:
            price_range += f"از {min_price:,}"
        if max_price:
            if min_price:
                price_range += f" تا {max_price:,}"
            else:
                price_range += f"تا {max_price:,}"
        price_range += " تومان"
        summary += f"\n{price_range}"
    
    summary += "\n\n⏳ لطفاً صبر کنید..."
    
    bot.send_message(chat_id, summary)
    
    # Start scraping in background
    threading.Thread(target=send_products, args=(product_name, count, chat_id, city, min_price, max_price)).start()
    
    # Reset user state
    user_states[user_id] = {}

def send_products(product_name, count, chat_id, city, min_price=None, max_price=None):
    try:
        products = scrape_divar_products(product_name, count, city, min_price, max_price)
        
        if not products:
            bot.send_message(chat_id, """❌ متأسفانه هیچ محصولی پیدا نشد

💡 پیشنهادات:
• کلمات جستجو را ساده‌تر کنید
• نام برند را حذف کنید
• محدوده قیمت را بررسی کنید
• شهر دیگری را امتحان کنید
• از کلمات مترادف استفاده کنید""")
            show_main_menu(chat_id)
            return
        
        bot.send_message(chat_id, f"✅ {len(products)} محصول پیدا شد! در حال ارسال...")
        
        for idx, product in enumerate(products, start=1):
            try:
                # Create clean message
                message = f"""📦 محصول {idx}:

🏷️ {product.get('title', 'بدون عنوان')}

💰 {product.get('price', 'قیمت نامشخص')}

📍 {product.get('meta', 'اطلاعات کامل در لینک موجود است')}"""
                
                if product.get('url'):
                    message += f"\n\n🔗 مشاهده آگهی: {product['url']}"
                
                # Send with image if available
                if product.get('image_url'):
                    try:
                        # Validate image URL before sending
                        img_url = product['image_url']
                        
                        # Test if image is accessible
                        img_response = requests.head(img_url, timeout=5)
                        if img_response.status_code == 200:
                            content_type = img_response.headers.get('content-type', '').lower()
                            if 'image' in content_type:
                                bot.send_photo(chat_id, img_url, caption=message[:1024], parse_mode=None)
                            else:
                                bot.send_message(chat_id, message)
                        else:
                            bot.send_message(chat_id, message)
                    
                    except Exception as e:
                        logger.error(f"Error sending image for product {idx}: {e}")
                        bot.send_message(chat_id, message)
                else:
                    bot.send_message(chat_id, message)
                
                # Small delay to avoid flooding
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error sending product {idx}: {e}")
                continue
        
        # Show completion message and main menu
        completion_msg = f"""✨ جستجو کامل شد!

📊 نتایج: {len(products)} محصول
🎯 محصول: {product_name}
🏙️ شهر: {CITIES_DATA.get(city, city)}

💡 برای جستجوی جدید از منوی زیر استفاده کنید:"""
        
        bot.send_message(chat_id, completion_msg)
        show_main_menu(chat_id)
        
    except Exception as e:
        logger.error(f"Error in send_products: {e}")
        bot.send_message(chat_id, "❌ خطایی در دریافت اطلاعات رخ داد. لطفاً دوباره تلاش کنید.")
        show_main_menu(chat_id)

# Error handler for bot polling
def main():
    while True:
        try:
            logger.info("🚀 Divar Bot is starting...")
            print("🚀 Bot is running and ready to search Divar!")
            bot.polling(none_stop=True, interval=0, timeout=30)
        except Exception as e:
            logger.error(f"Bot polling crashed: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()