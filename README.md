# A TeamSpeak 3 Music Bot
A straightforward bot for [TeamSpeak 3](https://www.teamspeak.com) capable of playing music from YouTube among other miscellaneous commands.

Built on [Python 3](https://www.python.org/) primarily using the [py-ts3](https://github.com/benediktschmitt/py-ts3), [pafy](https://pypi.org/project/pafy/), and [pyglet](https://bitbucket.org/pyglet/pyglet/wiki/Home) libraries.

## Setting Up the Bot

Clone the repository to your machine
```
git clone https://github.com/Vauxel/teamspeak-bot.git
cd teamspeak-bot
```

Install the requisite dependencies
```
pip install ts3
pip install youtube-dl
pip install pafy
pip install pyglet
pip install mutagen
```

Edit the global bot/server variables in `init.py`

Start the bot
```
python3 init.py
```