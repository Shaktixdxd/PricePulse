import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging to see what's happening
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# This function runs when the user sends /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # This creates the special button that requests the user's contact
    contact_button = KeyboardButton(text="Share My Phone Number", request_contact=True)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[contact_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "Hello! I'm a bot running live on a server. Please share your phone number to test.",
        reply_markup=keyboard,
    )

# This function runs when the bot receives a contact
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    phone_number = contact.phone_number
    user_id = contact.user_id
    first_name = contact.first_name

    # We'll log the received info to the console
    logger.info(f"Received contact from {first_name} (ID: {user_id}). Phone: {phone_number}")
    
    # Send a confirmation message back to the user
    await update.message.reply_text(
        f"Thank you, {first_name}! Your number ({phone_number}) was received by the bot running on the cloud!",
        reply_markup=ReplyKeyboardRemove() # This removes the special button
    )

def main() -> None:
    """This is the main function that starts the bot."""
    
    # Securely get the bot token from the server's environment variables
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("FATAL: BOT_TOKEN environment variable not set.")
        return

    # Set up the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add the handlers for the /start command and for receiving contacts
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # Start the bot
    logger.info("Bot is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()