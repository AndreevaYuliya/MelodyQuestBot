import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
import requests
import subprocess
import tempfile

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


LASTFM_API_KEY = '406aa82dbd905e099547e6cc67a515d6'

# Telegram bot token
TOKEN = '6085472614:AAFK0NPjzjPRajsDL4GnFZQaAmQyPH_PkSY'

# Genius API token
GENIUS_TOKEN = 'C0v_DU0tBb3oe4XzmlC0zW-Kj-BCJhNtobFQe4OS95h5G_ab1_MV7Yt9g2DCUZw1'

# Define a function for the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Welcome to the Music Search Bot!")

def search_music(query):
    api_key = '406aa82dbd905e099547e6cc67a515d6'
    api_url = 'http://ws.audioscrobbler.com/2.0/'

    params = {
        'method': 'track.search',
        'track': query,
        'api_key': api_key,
        'format': 'json'
    }

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        data = response.json()
        tracks = data.get('results', {}).get('trackmatches', {}).get('track', [])
        if tracks:
            return [track['name'] for track in tracks]

    return []

# Define a function for handling text messages
def handle_message(update, context):
    query = update.message.text
    results = search_music(query)

    if results:
        keyboard = []
        for result in results:
            # Create an InlineKeyboardButton for each music result
            button = InlineKeyboardButton(text=result, callback_data=result)
            keyboard.append([button])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the message with the inline keyboard
        update.message.reply_text(text="Select a music:", reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No results found.")


# Function to handle the callback from the button
def play_music(update, context, track):
    query = update.callback_query
    track = query.data
    audio_url = get_audio_url(track)

    if audio_url:
        # Download the audio file
        audio_data = download_audio(audio_url)
        

        if audio_data:
            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    
                    # Write the audio data to the temporary file
                    temp_file.write(audio_data)
                    
                    # Launch AIMP player with the temporary file
                    subprocess.run(['aimp', '/play', temp_file.name])                   

                # Send the audio file to the user
                context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(temp_file, "rb"))

            except Exception as e:
                logger.error(f"Failed to play music: {e}")
                context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to play music.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to play music.")



# Define a function for getting the audio URL of a track from Last.fm
def get_audio_url(track: str):
    api_url = 'http://ws.audioscrobbler.com/2.0/'

    params = {
        'method': 'track.getinfo',
        'track': track,
        'api_key': LASTFM_API_KEY,
        'format': 'json'
    }

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        data = response.json()
        track_info = data.get('track', {})
        audio = track_info.get('audio', {})
        audio_url = audio.get('url')
        return audio_url

    return None



# Define a function for downloading audio data from a URL
def download_audio(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return None


# Define a function to handle button presses
def button_handler(update, context):
    query = update.callback_query
    track = query.data
    play_music(update, context, track)



def main():
    # Set up the Telegram Bot API token
    token = '6085472614:AAFK0NPjzjPRajsDL4GnFZQaAmQyPH_PkSY'

    # Create the Updater and pass it your bot's token
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher


    # Register the start command handler
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(CommandHandler("play", play_music))


    # Register the message handler
    message_handler = MessageHandler(None, handle_message)
    dispatcher.add_handler(message_handler)
    
    

    # Register the callback query handler
    callback_query_handler = CallbackQueryHandler(button_handler)
    dispatcher.add_handler(callback_query_handler)
    
    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()

