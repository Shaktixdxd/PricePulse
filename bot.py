import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TARGET_CHAT_ID_1 = "https://t.me/+nyAefpjyXpw3YTg1"
TARGET_CHAT_ID_2 = "https://t.me/+PaKEPPClQpEyMThl"
TARGET_CHAT_ID_3 = "https://t.me/+epWUTCuzzkw3YTc9"
TARGET_CHAT_ID_4 = "https://t.me/c/2551597610/2"
TARGET_CHATS = [TARGET_CHAT_ID_1, TARGET_CHAT_ID_2, TARGET_CHAT_ID_3, TARGET_CHAT_ID_4]

# --- MESSAGES (You can customize these) ---
M1 = "Welcome to the bot! This is message M1."
M2 = "This is message M2, explaining the rules."
M3 = "This is message M3. Please choose an option below."
M4 = "Thank you for verifying! You are now a verified user. You can now use the MEDIA button."
M5 = "Verification cancelled. You can try again later by clicking the VERIFY button."
M6 = "You must be a verified user to send media. Please click the VERIFY button first."
M7 = "You are verified. Please send any media file you want to share."

# --- STATE MANAGEMENT ---
user_states = {}

def set_verified_status(user_id, status: bool):
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['verified'] = status
    logger.info(f"User {user_id} verification status set to {status}")

def is_verified(user_id) -> bool:
    return user_states.get(user_id, {}).get('verified', False)

# --- BOT HANDLERS ---
MENU, AWAITING_MEDIA = range(2)

async def forward_message_to_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    for chat_id in TARGET_CHATS:
        try:
            await context.bot.forward_message(
                chat_id=chat_id,
                from_chat_id=message.chat_id,
                message_id=message.message_id
            )
        except Exception as e:
            logger.error(f"Failed to forward message to {chat_id}. Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    set_verified_status(user_id, False)

    await update.message.reply_text(M1)
    await update.message.reply_text(M2)
    
    keyboard = [["RESTART", "MEDIA", "VERIFY"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(M3, reply_markup=reply_markup)
    
    return MENU

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    user_id = update.effective_user.id

    await forward_message_to_targets(update, context)

    if user_choice == "RESTART":
        return await start(update, context)

    elif user_choice == "VERIFY":
        contact_keyboard = KeyboardButton(text="Share Contact to Verify", request_contact=True)
        keyboard = [[contact_keyboard]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Please share your contact to complete verification.", reply_markup=reply_markup)
        return MENU

    elif user_choice == "MEDIA":
        if is_verified(user_id):
            await update.message.reply_text(M7)
            return AWAITING_MEDIA
        else:
            await update.message.reply_text(M6)
            return MENU

    return MENU

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles when the user shares their contact for verification."""
    user_id = update.effective_user.id
    contact = update.message.contact

    if contact:
        set_verified_status(user_id, True)
        await update.message.reply_text(M4)
        logger.info(f"User {user_id} verified with phone {contact.phone_number}")

    # FIXED: After verification, show the main menu again WITHOUT resetting the status
    keyboard = [["RESTART", "MEDIA", "VERIFY"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("You are now verified. Please choose an option from the menu.", reply_markup=reply_markup)
    
    return MENU

async def handle_media_and_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Thank you for your submission! Forwarding it now.")
    await forward_message_to_targets(update, context)
    return AWAITING_MEDIA

async def handle_unverified_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    if message.text:
        await forward_message_to_targets(update, context)
    else:
        await message.reply_text("Media is not allowed until you are verified. Please use the VERIFY button.")
    return MENU

def main() -> None:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("FATAL: BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                MessageHandler(filters.Regex("^(RESTART|MEDIA|VERIFY)$"), handle_menu_choice),
                MessageHandler(filters.CONTACT, handle_contact),
                MessageHandler(filters.ALL & ~filters.COMMAND, handle_unverified_messages),
            ],
            AWAITING_MEDIA: [
                MessageHandler(filters.Regex("^(RESTART)$"), start),
                MessageHandler(filters.ALL & ~filters.COMMAND, handle_media_and_text),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()