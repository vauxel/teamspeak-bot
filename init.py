# --------------------------------------------------
# Globals
# --------------------------------------------------
IP = "SERVER_IP_GOES_HERE"
PORT = 10011
PASSWORD = "SERVER_QUERY_PASSWORD"
BOTNAME = "BOT_USERNAME"

# --------------------------------------------------
# Modules
# --------------------------------------------------
import sys
import os
from subprocess import call
import random
import time
import threading
import ts3
from mutagen.easyid3 import EasyID3
from lib import youtube, music

# --------------------------------------------------
# Global Classes
# --------------------------------------------------
MusicManager = music.MusicManager(os.getcwd() + "\\res\\songs", os.getcwd() + "\\res\\playlists")

# --------------------------------------------------
# Functions
# --------------------------------------------------
class TS3Listener:
	def __init__(self, ip, port, user, password, nickname):
		self.nickname = nickname
		self.handler = None

		self.connection = ts3.query.TS3Connection(ip, port)
		self.connection.login(client_login_name=user, client_login_password=password)
		self.connection.use(sid=1)
		self.connection.keepalive(300)

		self.connection.clientupdate(client_nickname=nickname)
		print("TS3Listener initialized")
	def listen(self):
		self.connection.on_event.connect(self.eventhandler)
		self.connection.servernotifyregister(event="textserver")

		self.connection.recv_in_thread()
		print("TS3Listener listening")
	def deafen(self):
		self.connection.stop_recv()
		print("TS3Listener deafened (stopped listening)")
	def setHandler(self, handler):
		self.handler = handler
	def eventhandler(self, sender, event):
		if event.event == "notifytextmessage":
			if self.handler is not None:
				self.handler.handle(self, event.parsed[0]["invokerid"], event.parsed[0]["invokername"], event.parsed[0]["msg"])
class TS3Handler:
	def __init__(self):
		self.commands = [
			("Miscellaneous", [
				{"name": "Ping", "description": "Pong", "alias": ["ping"], "function": self.cmd_ping, "parameters": 0}
			]),
			("Music_Manager", [
				{"name": "Youtube Downloader", "description": "Download a YouTube video's audio to the song cache", "alias": ["youtube", "yt"], "function": self.cmd_youtube, "parameters": 1},
				{"name": "Add to Queue", "description": "Add a song to the queue from the song cache", "alias": ["add"], "function": self.cmd_queuemusic, "parameters": 1},
				{"name": "Add YT to Queue", "description": "Add a song to the queue from YouTube", "alias": ["addyt", "ytadd"], "function": self.cmd_queueytmusic, "parameters": 1},
				{"name": "Remove from Queue", "description": "Remove a song from the queue", "alias": ["remove"], "function": self.cmd_unqueuemusic, "parameters": 1},
				{"name": "Clear Queue", "description": "Clear the queue of all songs", "alias": ["clear"], "function": self.cmd_clearqueue, "parameters": 0},
				{"name": "Shuffle Queue", "description": "Shuffle the queue", "alias": ["shuffle"], "function": self.cmd_shufflequeue, "parameters": 0},
				{"name": "List Song Cache", "description": "List the songs in the song cache", "alias": ["list", "songs"], "function": self.cmd_listcache, "parameters": 0},
				{"name": "Search Song Cache", "description": "Search the song cache for songs with titles that contain a given keyword", "alias": ["search", "find"], "function": self.cmd_searchcache, "parameters": 1},
				{"name": "Load Playlist", "description": "Load playlist into the queue", "alias": ["load"], "function": self.cmd_loadplaylist, "parameters": 1},
				{"name": "Save Playlist", "description": "Save playlist from the queue", "alias": ["save"], "function": self.cmd_saveplaylist, "parameters": 2},
				{"name": "List Playlists", "description": "List available playlists", "alias": ["playlists"], "function": self.cmd_listplaylists, "parameters": 0}
			]),
			("Music_Player", [
				{"name": "Play", "description": "Play or resume the current song", "alias": ["play"], "function": self.cmd_playmusic, "parameters": 0},
				{"name": "Pause", "description": "Pause the currently playing song", "alias": ["pause"], "function": self.cmd_pausemusic, "parameters": 0},
				{"name": "Stop", "description": "Stop the currently playing song", "alias": ["stop"], "function": self.cmd_stopmusic, "parameters": 0},
				{"name": "Skip", "description": "Skip the current song", "alias": ["skip", "next"], "function": self.cmd_skipmusic, "parameters": 0},
				{"name": "Now Playing", "description": "Display the currently playing song", "alias": ["nowplaying", "np"], "function": self.cmd_nowplaying, "parameters": 0},
				{"name": "Set Volume", "description": "Set the music player's volume", "alias": ["volume", "vol"], "function": self.cmd_setvolume, "parameters": 1},
				{"name": "List Queue", "description": "List the current song queue", "alias": ["queue"], "function": self.cmd_listqueue, "parameters": 0}
			])
		]

		MusicManager.player.registeronplay(self.cmd_nowplaying)
	def handle(self, listener, senderid, sendername, message):
		self.listener = listener

		if message[0] == "!":
			self.handlecommand(senderid, sendername, message)
			return

		try:
			print("[Message] {0} ({1}): {2}".format(sendername, senderid, message).encode("ascii", errors="ignore").decode())
		except Exception as e:
			print("[Error] Message failed to print: %s" % e)
	def handlecommand(self, senderid, sendername, message):
		message = message[1:].split(" ")
		command = message[0]
		parameters = message[1:]

		try:
			print("[Command] {0} ({1}): {{{2}}} ({3})".format(sendername, senderid, command, parameters).encode("ascii", errors="ignore").decode())
		except Exception as e:
			print("[Error] Command failed to print: %s" % e)

		if command == "help":
			self.sendmessage("[b]╠════════╣[u]Teamspeak 3 Bot Commands[/u]╠════════╣[/b]")
			for category in self.commands:
				self.sendmessage("[u]{0}[/u]".format(category[0].replace("_", " ")))
				for cmd in category[1]:
					self.sendmessage("[b]{0:<30}[/b] {1} § [i]{2}[/i]:".format(cmd["name"], str(cmd["alias"]), cmd["description"]))
			return

		for category in self.commands:
			for cmd in category[1]:
				if command in cmd["alias"]:
					if cmd["parameters"] == -1 or len(parameters) == cmd["parameters"]:
						cmd["function"](*parameters)
					else:
						self.sendmessage("Invalid command parameters")
					break
	def sendcommand(self, command, **parameters):
		try:
			getattr(self.listener.connection, command)(**parameters)
		except:
			self.sendmessage("An error occurred in the bot")
	def sendmessage(self, message):
		self.sendcommand("sendtextmessage", targetmode=3, target=1, msg=message)
	def ytdownloadcallback(total, recvd, ratio, rate, eta):
		size = total
		for unit in ["bytes", "KiB", "MiB", "GiB", "TiB"]:
			if abs(size) < 1024.0:
				sizeunit = unit
				break
			else:
				size /= 1024.0

		self.sendmessage("[b]/♫/ YouTube /♫/[/b] Downloading :: Size ({0:.2f} {1})  Speed ({2} KB/s)  ETA ({3}s)".format(size, sizeunit, rate, eta))
	def cmd_ping(self):
		self.sendmessage("Pong")
	def cmd_youtube(self, url):
		url = url.replace("[URL]", "").replace("[/URL]", "").replace("https", "http")

		try:
			parser = youtube.YTParser(url)
			self.sendmessage("[b]/♫/ YouTube /♫/[/b] Processing ([i]{0}[/i])...".format(parser.video.title))
			songid = parser.parseaudio()
			self.sendmessage("[b]/♫/ YouTube /♫/[/b] Finished processing {{{0}}}".format(songid))
		except:
			self.sendmessage("[b]/♫/ YouTube /♫/[/b] Invalid YouTube ID given (Example: [?v=dQw4w9WgXcQ] without the [?v=])")
	def cmd_queueytmusic(self, url):
		url = url.replace("[URL]", "").replace("[/URL]", "").replace("https", "http")

		try:
			parser = youtube.YTParser(url)
			self.sendmessage("[b]/♫/ YouTube /♫/[/b] Processing ([i]{0}[/i])...".format(parser.video.title))
			songid = parser.parseaudio()
			MusicManager.addsong(songid)
			self.sendmessage("[b]/♫/ YouTube /♫/[/b] Added [[i]{0}[/i]] {{{1}}} to the song queue".format(parser.video.title, songid))
		except:
			self.sendmessage("[b]/♫/ YouTube /♫/[/b] Invalid YouTube ID given (Example: [?v=dQw4w9WgXcQ] without the [?v=])")
	def cmd_queuemusic(self, songid):
		try:
			MusicManager.addsong(songid)
			self.sendmessage("[b]/♫/ Queue /♫/[/b] Added [[i]{0}[/i]] {{{1}}} to the song queue".format(MusicManager.getsongtitle(songid), songid))
		except:
			self.sendmessage("[b]/♫/ Queue /♫/[/b] Invalid song ID given (Example: {78fv}). Get song IDs from (!list or !search)")
	def cmd_unqueuemusic(self, songid):
		try:
			MusicManager.removesong(songid)
			self.sendmessage("[b]/♫/ Queue /♫/[/b] Removed [[i]{0}[/i]] {{{1}}} from the song queue".format(MusicManager.getsongtitle(songid), songid))
		except:
			self.sendmessage("[b]/♫/ Queue /♫/[/b] Invalid song ID given (Example: {78fv}). Get song IDs from (!list or !search)")
	def cmd_clearqueue(self):
		queuelen = len(MusicManager.player.getqueue())
		MusicManager.player.clearqueue()
		self.sendmessage("[b]/♫/ Queue /♫/[/b] Queue of [u]{0}[/u] songs successfully cleared".format(queuelen))
	def cmd_shufflequeue(self):
		MusicManager.player.shuffle()
		self.sendmessage("[b]/♫/ Queue /♫/[/b] Queue of [u]{0}[/u] songs shuffled".format(len(MusicManager.player.getqueue())))
	def cmd_playmusic(self):
		MusicManager.player.play()
	def cmd_pausemusic(self):
		MusicManager.player.pause()
	def cmd_stopmusic(self):
		MusicManager.player.stop()
	def cmd_skipmusic(self):
		self.sendmessage("[b]/♫/ Player /♫/[/b] Skipping...")
		MusicManager.player.skip()
	def cmd_nowplaying(self):
		if not MusicManager.player.isplaying():
			self.sendmessage("[b]/♫/ Now Playing /♫/[/b] There is no song currently playing")
		else:
			time_raw = MusicManager.player.gettime()
			time_m, time_s = divmod(time_raw, 60)
			time_h, time_m = divmod(time_m, 60)
			time = "%d:%02d:%02d" % (time_h, time_m, time_s)

			duration_raw = MusicManager.player.getduration()
			duration_m, duration_s = divmod(duration_raw, 60)
			duration_h, duration_m = divmod(duration_m, 60)
			duration = "%d:%02d:%02d" % (duration_h, duration_m, duration_s)

			complete = "{:0>3.0%}".format(time_raw / duration_raw)

			if time_raw == 0:
				self.sendmessage("[b]/♫/ Now Playing /♫/[/b] [i]{0}[/i]".format(MusicManager.getsongtitle(MusicManager.player.getnp()[0])))
			else:
				self.sendmessage("[b]/♫/ Now Playing /♫/[/b] [i]{0}[/i] ({1} / {2} [{3}])".format(MusicManager.getsongtitle(MusicManager.player.getnp()[0]), time, duration, complete))
	def cmd_setvolume(self, volume):
		volume = float(volume)

		if volume < 0.1 or volume > 1.0:
			self.sendmessage("[b]/♫/ Player /♫/[/b] Invalid volume given (0.1 to 1.0)")
			return

		try:
			MusicManager.player.setvolume(volume)
		except:
			self.sendmessage("You dun' goofed")

		self.sendmessage("[b]/♫/ Player /♫/[/b] Volume set to [u]{0}[/u]".format(volume))
	def cmd_listqueue(self):
		queue = MusicManager.player.getqueue()
		queuelen = len(queue)

		if queuelen == 0:
			self.sendmessage("[b]/♫/ Queue /♫/[/b] There are no songs in the queue")
			return

		self.sendmessage("[b]/♫/ Queue /♫/[/b] There are [u]{0}[/u] songs in the queue:".format(queuelen))

		index = 1
		for songid, songfile in queue:
			title = MusicManager.getsongtitle(songid)
			if index == 1 and MusicManager.player.isplaying():
				self.sendmessage("[b][{0} (NP)][/b] {{{1}}} § [i]{2}[/i]".format(index, songid, title))
			else:
				self.sendmessage("[b][{0}][/b] {{{1}}} § [i]{2}[/i]".format(index, songid, title))
			index += 1
	def cmd_listcache(self):
		songs = MusicManager.getsongs()
		self.sendmessage("[b]/♫/ Cache /♫/[/b] There are [u]{0}[/u] songs in the cache:".format(len(songs)))

		index = 1
		for songid, songfile in songs:
			self.sendmessage("[b][{0}][/b] {{{1}}} § [i]{2}[/i]".format(index, songid, MusicManager.getsongtitle(songid)))
			index += 1
	def cmd_searchcache(self, keyword):
		songmatches = []

		index = 1
		for songid, songfile in MusicManager.getsongs():
			title = MusicManager.getsongtitle(songid)

			if title.find(keyword) != -1:
				songmatches.append("[b][{0}][/b] {{{1}}} § [i]{2}[/i]".format(index, songid, title))
				index += 1

		matchescount = len(songmatches)
		self.sendmessage("[b]/♫/ Cache /♫/[/b] There {0} [u]{1}[/u] song{2} matching the keyword [u]{3}[/u] in the cache:".format("was" if matchescount == 1 else "were", matchescount, "" if matchescount == 1 else "s", keyword))

		for match in songmatches:
			self.sendmessage(match)
	def cmd_loadplaylist(self, playlistid):
		if not MusicManager.player.isempty():
			self.sendmessage("[b]/♫/ Playlist /♫/[/b] Can't load a playlist into a non-empty queue")
			return

		try:
			count = MusicManager.loadplaylist(playlistid)
			queuelen = len(MusicManager.player.getqueue())

			if queuelen == count:
				self.sendmessage("[b]/♫/ Playlist /♫/[/b] Playlist of [u]{0}[/u] song{1} successfully loaded into the queue".format(count, "" if count == 1 else "s"))
			else:
				self.sendmessage("[b]/♫/ Playlist /♫/[/b] Playlist of [u]{0}[/u] song{1} loaded into the queue. [u]{2}[/u] songs failed to load".format(count, "" if count == 1 else "s", count - queuelen))
		except:
			self.sendmessage("[b]/♫/ Playlist /♫/[/b] A playlist by the id [u]{0}[/u] does not exist".format(playlistid))
	def cmd_saveplaylist(self, playlistid, name):
		#if MusicManager.player.isempty():
		#	self.sendmessage("[b]/♫/ Playlist /♫/[/b] Can't save an empty queue as a playlist")
		#	return

		try:
			count = MusicManager.saveplaylist(playlistid, name.replace("_", " "), overwrite=True)
			self.sendmessage("[b]/♫/ Playlist /♫/[/b] Playlist of [u]{0}[/u] song{1} saved as [u]{2}[/u]".format(count, "" if count == 1 else "s", playlistid))
		except:
			self.sendmessage("[b]/♫/ Playlist /♫/[/b] A playlist by the id [u]{0}[/u] already exists".format(playlistid))
	def cmd_listplaylists(self):
		playlists = MusicManager.getplaylists()
		playlistslen = len(playlists)
		self.sendmessage("[b]/♫/ Playlist /♫/[/b] There {0} [u]{1}[/u] saved playlist{2}:".format("is" if playlistslen == 1 else "are", playlistslen, "" if playlistslen == 1 else "s"))

		index = 1
		for playlistid, playlistfile in playlists:
			self.sendmessage("[b][{0}][/b] [u]{1}[/u] § [i]{2}[/i]".format(index, playlistid, MusicManager.getplaylistname(playlistid)))
			index += 1

# --------------------------------------------------
# Main Program
# --------------------------------------------------
print("Starting Program...")
ts3handler = TS3Handler()
ts3listener = TS3Listener(IP, PORT, "ServerAdmin", PASSWORD, BOTNAME)
ts3listener.setHandler(ts3handler)
ts3listener.listen()