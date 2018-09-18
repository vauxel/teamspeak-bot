# --------------------------------------------------
# Modules
# --------------------------------------------------
import os
import threading
from random import shuffle
import pyglet
from mutagen.easyid3 import EasyID3

# --------------------------------------------------
# Class
# --------------------------------------------------
class MusicPlayer:
	def __init__(self):
		self.volume = 1
		self.sourcequeue = []
		self.currentsource = None
		self.currentplayer = None
	def registeronplay(self, callablefunc):
		self.onplaycall = callablefunc
	def checkend(self):
		if not self.isplaying():
			return

		if self.gettime() >= (self.getduration() - 0.5):
			threading.Timer(2.5, self.skip).start()
		else:
			threading.Timer(0.25, self.checkend).start()
	def getqueue(self):
		return self.sourcequeue
	def isempty(self):
		return len(self.sourcequeue) == 0
	def isplaying(self):
		if self.currentplayer is None:
			return False

		return self.currentplayer.playing
	def getnp(self):
		if not self.isplaying():
			return ""

		return self.sourcequeue[0]
	def gettime(self):
		if self.currentplayer is None:
			return

		return self.currentplayer.time
	def getduration(self):
		if self.currentsource is None:
			return

		return self.currentsource.duration
	def getvolume(self):
		if self.currentplayer is None:
			return

		return self.currentplayer.volume
	def setvolume(self, level):
		if self.currentplayer is None:
			return

		#if level < 0 or level > 1:
		#	return

		self.currentplayer.volume = level
	def queue(self, songid, file):
		self.sourcequeue.append((songid, file))
	def unqueue(self, songid):
		found = -1
		index = 0

		for source in self.sourcequeue():
			if source[0] == songid:
				found = index
				break
			else:
				index += 1

		if found == -1:
			raise KeyError("Song ID could not be found in queue")

		if found == 0:
			self.stop()

		self.sourcequeue.pop(found)
	def clearqueue(self):
		self.stop()
		self.sourcequeue = []
	def shufflequeue(self):
		if self.isempty():
			return

		if self.isplaying():
			npsong = self.sourcequeue[0]
			self.sourcequeue.pop(0)

		shuffle(self.sourcequeue)

		if npsong is not None:
			self.sourcequeue.insert(0, npsong)
	def play(self):
		if self.isempty() or self.isplaying():
			return

		if self.currentplayer is None:
			try:
				self.currentsource = pyglet.media.load(self.sourcequeue[0][1])
				self.currentplayer = self.currentsource.play()
				self.currentplayer.volume = self.volume
			except:
				self.skip()
				return

			if self.onplaycall is not None:
				self.onplaycall()
		else:
			self.currentplayer.play()

		self.checkend()
	def pause(self):
		if not self.isplaying():
			return

		self.currentplayer.pause()
	def stop(self):
		if self.currentplayer is None:
			return

		self.currentplayer.delete()
		self.currentplayer = None
		self.currentsource = None
	def skip(self):
		if self.currentplayer is not None:
			self.stop()
			self.sourcequeue.pop(0)

		if not self.isempty():
			self.play()
class MusicManager:
	def __init__(self, songdir, playlistdir):
		self.songdir = songdir
		self.playlistdir = playlistdir

		self.player = MusicPlayer()
	def getsongdir(self):
		return self.songdir
	def getplaylistdir(self):
		return self.playlistdir
	def getsongs(self):
		songs = []
		for song in os.listdir(self.getsongdir()):
			songs.append((song[:-4], self.getsongdir() + "\\" + song))
		return songs
	def getsongtitle(self, songid):
		return EasyID3(self.getsongdir() + "\\" + songid + ".mp3")["title"][0]
	def addsong(self, songid):
		f = self.getsongdir() + "\\" + songid + ".mp3"
		if not os.path.isfile(f):
			raise FileNotFoundError("Song file could not be found: %s" % f)
		else:
			self.player.queue(songid, f)
	def removesong(self, songid):
		f = self.getsongdir() + "\\" + songid + ".mp3"
		if not os.path.isfile(f):
			raise FileNotFoundError("Song file could not be found: %s" % f)
		else:
			self.player.unqueue(songid)
	def getplaylists(self):
		playlists = []
		for playlist in os.listdir(self.getplaylistdir()):
			playlists.append((playlist[:-3], self.getplaylistdir() + "\\" + playlist))
		return playlists
	def playlistexists(self, playlistid):
		return os.path.isfile(self.getplaylistdir() + "\\" + playlistid + ".pl")
	def getplaylistname(self, playlistid):
		f = open(self.getplaylistdir() + "\\" + playlistid + ".pl", "r")
		return f.readline()[1:].rstrip()
	def loadplaylist(self, playlistid):
		if not self.playlistexists(playlistid):
			raise FileNotFoundError("Playlist file does not exist: %s" % file)

		count = 0
		f = open(self.getplaylistdir() + "\\" + playlistid + ".pl", "r")

		for line in f:
			if line[0] == "@":
				continue

			count += 1

			try:
				self.addsong(line.rstrip())
			except:
				continue

		return count
	def saveplaylist(self, playlistid, name, overwrite=False):
		if not overwrite and self.playlistexists(playlistid):
			raise FileExistsError("Playlist file already exists: %s" % file)

		f = open(self.getplaylistdir() + "\\" + playlistid + ".pl", "w")
		f.write("@" + name + "\n")

		count = 0
		songs = self.player.getqueue()
		for song in songs:
			f.write(song[0] + "\n")
			count += 1

		return count