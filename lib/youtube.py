# --------------------------------------------------
# Modules
# --------------------------------------------------
import os
from subprocess import call
import hashlib
import pafy
from mutagen.easyid3 import EasyID3

OUTPUT_DIR = os.getcwd() + "\\res\\songs\\"
OUTPUT_EXT = "mp3"
OUTPUT_CODEC = "libmp3lame"

# --------------------------------------------------
# Class
# --------------------------------------------------
class YTParser:
	def __init__(self, url):
		self.video = pafy.new(url, basic=True, gdata=False)
		self.audio = self.video.getbestaudio()
		self.hashedname = hashlib.sha256(self.video.title.encode()).hexdigest()[:4]

		self.rawaudiofile = OUTPUT_DIR + self.hashedname + "." + self.audio.extension
		self.audiofile = OUTPUT_DIR + self.hashedname + "." + OUTPUT_EXT
	def downloadaudio(self, callback=None):
		try:
			self.audio.download(filepath=self.rawaudiofile, quiet=True, callback=callback)
		except:
			print("File (" + self.hashedname + ") failed to download")
	def convertaudio(self):
		try:
			call(["ffmpeg",
				"-v", "quiet",
				"-i", self.rawaudiofile,
				"-acodec", OUTPUT_CODEC,
				"-aq", "4",
				self.audiofile
			])
		except:
			print("File (" + self.hashedname + ") failed to be converted")

		try:
			os.remove(self.rawaudiofile)
			self.rawaudiofile = None
		except:
			print("File (" + self.hashedname + ") failed to be deleted")
	def tagaudio(self):
		try:
			audiofile = EasyID3(self.audiofile)
			audiofile["title"] = self.video.title
			audiofile.save()
		except:
			print("File (" + self.hashedname + ") failed to be tagged")
	def parseaudio(self, callback=None):
		# Check for existing converted audio
		if os.path.isfile(self.audiofile):
			return self.hashedname
		else:
			# Download before converting
			if not os.path.isfile(self.rawaudiofile):
				self.downloadaudio(callback=callback)

			# Convert downloaded audio
			self.convertaudio()

			if not os.path.isfile(self.audiofile):
				self.audiofile = None
			else:
				self.tagaudio()

			return self.hashedname