import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# --- CONFIGURATION ---
# Your Token
TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4" 

# USGS API URL (All earthquakes in the past hour)
EARTHQUAKE_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

# Store sent earthquake IDs to avoid duplicate alerts
sent_earthquake_ids = set()

# Store chat IDs of users who start the bot
subscribed_users = set()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and subscribes the user to alerts."""
    chat_id = update.effective_chat.id
    subscribed_users.add(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ **Earthquake Bot Started!**\n\nI will check the USGS data every minute and notify you of new earthquakes."
    )

async def check_earthquakes(context: ContextTypes.DEFAULT_TYPE):
    """Fetches earthquake data and sends alerts."""
    global sent_earthquake_ids
    
    try:
        response = requests.get(EARTHQUAKE_API_URL)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])

            # Iterate through earthquakes
            for quake in features:
                properties = quake['properties']
                quake_id = quake['id']
                magnitude = properties['mag']
                place = properties['place']
                url = properties['url']
                
                # Filter: Only alert for magnitude > 2.0 (Optional, prevents spam for tiny tremors)
                if magnitude is not None and magnitude >= 2.0:
                    
                    # If we haven't seen this earthquake yet
                    if quake_id not in sent_earthquake_ids:
                        message = (
                            f"🚨 **EARTHQUAKE ALERT** 🚨\n\n"
                            f"📉 **Magnitude:** {magnitude}\n"
                            f"📍 **Location:** {place}\n"
                            f"🔗 [More Info]({url})"
                        )

                        # Send to all subscribed users
                        for chat_id in subscribed_users:
                            try:
                                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                            except Exception as e:
                                print(f"Could not send to {chat_id}: {e}")

                        # Remember this quake so we don't alert again
                        sent_earthquake_ids.add(quake_id)
                        
    except Exception as e:
        print(f"Error fetching earthquake data: {e}")

if __name__ == '__main__':
    # Build the application
    application = ApplicationBuilder().token(TOKEN).build()

    # Add the command handler
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Set up the Job Queue to check for earthquakes every 60 seconds
    job_queue = application.job_queue
    job_queue.run_repeating(check_earthquakes, interval=60, first=10)

    # Run the bot
    print("Bot is running...")
    application.run_polling()
