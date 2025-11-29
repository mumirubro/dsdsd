import logging
import asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import os
from main import PayPalProcessor

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin configuration
ADMIN_ID = 1805944073
ADMIN_USERNAME = "mumiru"

def is_admin(user_id: int, username: str = None) -> bool:
    """Check if user is admin"""
    if user_id == ADMIN_ID:
        return True
    if username and username.lower() == ADMIN_USERNAME.lower():
        return True
    return False

# Initialize PayPal processor
processor = PayPalProcessor()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler"""
    welcome_text = """
🤖 <b>PayPal Card Checker Bot</b>

<b>Commands:</b>
• <code>/pp CARD|MM|YYYY|CVV</code> - Check single card
  Example: <code>/pp 4987780029794225|06|2030|455</code>

• <code>/mpp</code> - Mass check (send file after command)
  Send a .txt file with cards (one per line)

• <code>/mpp CARD|MM|YYYY|CVV [CARD2|...] </code> - Direct mass check (max 5 cards)
  Example: <code>/mpp 4987780029794225|06|2030|455 4532111111111111|12|2025|123</code>

<b>File format example (.txt):</b>
<code>4987780029794225|06|2030|455
4532111111111111|12|2025|123
5555555555554444|03|2026|789</code>

Limit: 5 cards per mass check (unlimited for admins)
    """
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


async def check_single(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle single card check with /pp command"""
    if not context.args:
        await update.message.reply_text("❌ Usage: <code>/pp CARD|MM|YYYY|CVV</code>", parse_mode=ParseMode.HTML)
        return
    
    card_data = context.args[0]
    
    try:
        parts = card_data.split('|')
        if len(parts) != 4:
            await update.message.reply_text("❌ Invalid format. Use: <code>CARD|MM|YYYY|CVV</code>", parse_mode=ParseMode.HTML)
            return
        
        cc, mm, yyyy, cvv = parts
        
        # Validate
        if not (len(cc) >= 13 and len(cc) <= 19 and cc.isdigit()):
            await update.message.reply_text("❌ Invalid card number", parse_mode=ParseMode.HTML)
            return
        if not (mm.isdigit() and 1 <= int(mm) <= 12):
            await update.message.reply_text("❌ Invalid month (01-12)", parse_mode=ParseMode.HTML)
            return
        if not (yyyy.isdigit() and len(yyyy) == 4):
            await update.message.reply_text("❌ Invalid year (YYYY format)", parse_mode=ParseMode.HTML)
            return
        if not (cvv.isdigit() and 3 <= len(cvv) <= 4):
            await update.message.reply_text("❌ Invalid CVV (3-4 digits)", parse_mode=ParseMode.HTML)
            return
        
        await update.message.reply_text("⏳ Checking card...", parse_mode=ParseMode.HTML)
        
        # Run in executor to avoid blocking
        result = await asyncio.to_thread(processor.process_payment, cc, mm, yyyy, cvv)
        
        response = f"{result['emoji']} <b>{result['status']}</b>\n{result['msg']}"
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}", parse_mode=ParseMode.HTML)


async def check_mass_direct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle mass card check with direct input or file"""
    user_id = update.effective_user.id
    username = update.effective_user.username if update.effective_user else None
    
    if context.args:
        # Direct mass check
        cards_data = context.args
        
        if len(cards_data) > 5 and not is_admin(user_id, username):
            await update.message.reply_text("❌ Maximum 5 cards allowed per check for users! (Admins have unlimited access)", parse_mode=ParseMode.HTML)
            return
        
        await update.message.reply_text(f"⏳ Checking {len(cards_data)} card(s)...", parse_mode=ParseMode.HTML)
        
        results = []
        for idx, card_data in enumerate(cards_data, 1):
            try:
                parts = card_data.split('|')
                if len(parts) != 4:
                    results.append(f"❌ Card {idx}: Invalid format")
                    continue
                
                cc, mm, yyyy, cvv = parts
                
                # Validate
                if not (len(cc) >= 13 and len(cc) <= 19 and cc.isdigit()):
                    results.append(f"❌ Card {idx}: Invalid card number")
                    continue
                if not (mm.isdigit() and 1 <= int(mm) <= 12):
                    results.append(f"❌ Card {idx}: Invalid month")
                    continue
                if not (yyyy.isdigit() and len(yyyy) == 4):
                    results.append(f"❌ Card {idx}: Invalid year")
                    continue
                if not (cvv.isdigit() and 3 <= len(cvv) <= 4):
                    results.append(f"❌ Card {idx}: Invalid CVV")
                    continue
                
                # Check card
                result = await asyncio.to_thread(processor.process_payment, cc, mm, yyyy, cvv)
                results.append(f"{result['emoji']} Card {idx}: {result['msg']}")
                
            except Exception as e:
                results.append(f"❌ Card {idx}: Error - {str(e)}")
        
        response = "\n".join(results)
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
    
    else:
        # Wait for file
        context.user_data['waiting_for_file'] = True
        is_user_admin = is_admin(user_id, username)
        limit_msg = "max 5 cards for users, unlimited for admins" if not is_user_admin else "unlimited for admins"
        await update.message.reply_text(f"📁 Send a .txt file with cards (one per line, {limit_msg})", parse_mode=ParseMode.HTML)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document (file) upload for mass check"""
    if not context.user_data.get('waiting_for_file'):
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username if update.effective_user else None
    
    document = update.message.document
    
    # Check file type
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Please send a .txt file", parse_mode=ParseMode.HTML)
        return
    
    try:
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_content = await file.download_as_bytearray()
        cards_text = file_content.decode('utf-8').strip()
        
        cards_data = [line.strip() for line in cards_text.split('\n') if line.strip()]
        
        if len(cards_data) > 5 and not is_admin(user_id, username):
            await update.message.reply_text("❌ Maximum 5 cards allowed per check for users! (Admins have unlimited access)", parse_mode=ParseMode.HTML)
            return
        
        if len(cards_data) == 0:
            await update.message.reply_text("❌ No cards found in file", parse_mode=ParseMode.HTML)
            return
        
        await update.message.reply_text(f"⏳ Checking {len(cards_data)} card(s)...", parse_mode=ParseMode.HTML)
        
        results = []
        for idx, card_data in enumerate(cards_data, 1):
            try:
                parts = card_data.split('|')
                if len(parts) != 4:
                    results.append(f"❌ Card {idx}: Invalid format")
                    continue
                
                cc, mm, yyyy, cvv = parts
                
                # Validate
                if not (len(cc) >= 13 and len(cc) <= 19 and cc.isdigit()):
                    results.append(f"❌ Card {idx}: Invalid card number")
                    continue
                if not (mm.isdigit() and 1 <= int(mm) <= 12):
                    results.append(f"❌ Card {idx}: Invalid month")
                    continue
                if not (yyyy.isdigit() and len(yyyy) == 4):
                    results.append(f"❌ Card {idx}: Invalid year")
                    continue
                if not (cvv.isdigit() and 3 <= len(cvv) <= 4):
                    results.append(f"❌ Card {idx}: Invalid CVV")
                    continue
                
                # Check card
                result = await asyncio.to_thread(processor.process_payment, cc, mm, yyyy, cvv)
                results.append(f"{result['emoji']} Card {idx}: {result['msg']}")
                
            except Exception as e:
                results.append(f"❌ Card {idx}: Error - {str(e)}")
        
        response = "\n".join(results)
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
        context.user_data['waiting_for_file'] = False
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error reading file: {str(e)}", parse_mode=ParseMode.HTML)
        context.user_data['waiting_for_file'] = False


async def main() -> None:
    """Start the bot"""
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        print("Please set it using: replit secrets")
        return
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pp", check_single))
    application.add_handler(CommandHandler("mpp", check_mass_direct))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Start the Bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Bot started and polling...")
    
    # Run until you send an interrupt signal
    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Bot stopped")
