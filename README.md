# MCBot
Simple minecraft server monitoring discord bot.

## Installation
1. `git clone https://github.com/TheyuGin/MCBot.git`
1. Install requirements accordingly to [requirements.txt](/requriements.txt):
  1. Create python virtualenv with `virutalenv venv`
  1. `source venv/bin/activate`
  1. `pip install -r requirements.txt`
1. Make sure you have set the environment variable MCBOT_TOKEN according to bot token you created in your discord dev dashboard.
1. `python main.py`

## Usage
* Creating an updating message with server info: `mcbot createmessage`
* Adding a minecraft server to monitor: `mcbot addserver` (the bot will promt you with what message to add server to)
* Deleting server: `mcbot removeserver`
* Deleting a message from your server: `mcbot removemessage`
