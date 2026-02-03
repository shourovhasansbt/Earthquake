import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, Application

# --- CONFIGURATION ---
TOKEN = "8288219297:AAGCB3pxmy3DzXiVTpCRsgaIeJ9_rT1jfJ4" 
EARTHQUAKE_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

# Store data
sent_earthquake_ids = set()
subscribed_users = set()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribed_users.add(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ **Earthquake Bot Started!**\n\nI will check USGS data every minute."
    )

async def check_earthquakes_logic(app):
    """The logic to fetch data and send messages."""
    global sent_earthquake_ids
    try:
        response = requests.get(EARTHQUAKE_API_URL)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])

            for quake in features:
                properties = quake['properties']
                quake_id = quake['id']
                magnitude = properties['mag']
                place = properties['place']
                url = properties['url']
                
                # Filter: Magnitude > 2.0
                if magnitude is not None and magnitude >= 2.0:
                    if quake_id not in sent_earthquake_ids:
                        message = (
                            f"🚨 **EARTHQUAKE ALERT** 🚨\n\n"
                            f"📉 **Magnitude:** {magnitude}\n"
                            f"📍 **Location:** {place}\n"
                            f"🔗 [More Info]({url})"
                        )
                        for chat_id in subscribed_users:
                            try:
                                await app.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                            except Exception as e:
                                print(f"Failed to send to {chat_id}: {e}")
                        
                        sent_earthquake_ids.add(quake_id)
    except Exception as e:
        print(f"Error: {e}")

async def background_loop(application):
    """Runs the check every 60 seconds without JobQueue."""
    while True:
        await check_earthquakes_logic(application)
        await asyncio.sleep(60)

async def post_init(application: Application):
    """Starts the background loop when bot starts."""
    asyncio.create_task(background_loop(application))

if __name__ == '__main__':
    # We add post_init to start our custom loop
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler('start', start))

    print("Bot is running...")
    application.run_polling()
