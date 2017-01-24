import curses
import time
import threading
from __builtin__ import True

class zone:
	def __init__ (self, parent, zoneName, height, width, y, x, volume, inGroup, mute):
		# Parameters
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.zoneName = zoneName
		self.volume = volume
		self.inGroup = inGroup
		self.mute = mute
		self.win = parent.subwin(self.height, self.width, self.y, self.x)
		self.win.box()
		self.active = False
		self.enabled = True
		# UI details
		self.vOffset = 2
		self.hOffset = 2
		# Usability parameters
		self.volDelta = 5
		self.minVolume = 0
		self.maxVolume = 127

		self.drawWindow()

	def drawZoneName(self):
		self.win.addstr(self.vPosZoneName, self.hPosZoneName, self.zoneName, curses.A_STANDOUT if self.active else curses.A_NORMAL)

	def drawVolume(self):
		self.win.addstr(self.vPosVolume, self.hPosVolume, "Vol.: {}".format(self.volume))

	def drawInGroup(self):
		self.win.addstr(self.vPosInGroup, self.hPosInGroup, "In group", curses.A_BOLD if self.inGroup else curses.A_DIM)

	def drawMute(self):
		self.win.addstr(self.vPosMute, self.hPosMute, "Mute", curses.A_BOLD if self.mute else curses.A_DIM)

	def drawWindow(self):
		vPos = 0

		vPos += self.vOffset
		self.vPosZoneName = vPos
		self.hPosZoneName = self.hOffset
		self.drawZoneName()

		vPos += self.vOffset
		self.vPosVolume = vPos
		self.hPosVolume = self.hOffset
		self.drawVolume()

		vPos += self.vOffset
		self.vPosInGroup = vPos
		self.hPosInGroup = self.hOffset
		self.drawInGroup()

		self.vPosMute = vPos + self.vOffset
		self.hPosMute = self.hOffset
		self.drawMute()

		self.win.refresh()

	def toggleInGroup(self):
		if not self.enabled:
			return

		self.inGroup = not self.inGroup

		self.drawInGroup()
		self.win.refresh()

	def toggleMute(self):
		if not self.enabled:
			return

		self.mute = not self.mute

		self.drawMute()
		self.win.refresh()

	def toggleActive(self):
		self.active = not self.active

		self.drawZoneName()
		self.win.refresh()

	def incrVolume(self):
		if not self.enabled:
			return

		prevVolume = self.volume
		self.volume += self.volDelta
		if self.volume > self.maxVolume:
			self.volume = self.maxVolume
		#elif self.volume % self.volDelta != 0:
		#	self.volume -= self.volume % self.volDelta
			

		if self.volume == prevVolume:
			return

		self.drawVolume()
		self.win.refresh()

	def decrVolume(self):
		if not self.enabled:
			return

		prevVolume = self.volume
		self.volume -= self.volDelta
		if self.volume < self.minVolume:
			self.volume = self.minVolume
		#elif self.volume % self.volDelta != 0:
		#	self.volume += self.volume % self.volDelta

		if self.volume == prevVolume:
			return

		self.drawVolume()
		self.win.refresh()

	def disableZone(self):
		self.enabled = False
		self.win.bkgd('/')
		self.drawWindow()

	def enableZone(self):
		self.enabled = True
		self.win.bkgd(' ')
		self.drawWindow()

	def resetParams(self, volume = None, mute = None, inGroup = None):
		redraw = False
		if volume is not None:
			self.volume = volume
			redraw = True
		if mute is not None:
			self.mute = mute
			redraw = True
		if inGroup is not None:
			self.inGroup = inGroup
			redraw = True

		if redraw:
			self.drawWindow()

class globalControls:
	def __init__(self, parent, height, width, y, x):
		# Parameters
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.win = parent.subwin(self.height, self.width, self.y, self.x)
		self.win.box()
		# UI details
		self.vOffset = 2
		self.hOffset = 2
		# Usability parameters
		self.highlightDuration = 0.3 # seconds

		self.onPlayPause = False
		self.onStartRadio= False
		
		self.drawWindow()

	def drawPlayPause(self):
		self.win.addstr(self.vPosPlayPause, self.hPosPlayPause, "Play/Pause", curses.A_STANDOUT if self.onPlayPause else curses.A_NORMAL)

	def drawStartRadio(self):
		self.win.addstr(self.vPosStartRadio, self.hPosStartRadio, "Start Radio", curses.A_STANDOUT if self.onStartRadio else curses.A_NORMAL)

	def drawWindow(self):
		vPos = 0

		vPos += self.vOffset
		self.vPosPlayPause = vPos
		self.hPosPlayPause = self.hOffset
		self.drawPlayPause()

		vPos += self.vOffset
		self.vPosStartRadio = vPos
		self.hPosStartRadio = self.hOffset
		self.drawStartRadio()

		self.win.refresh()

	def pressPlayPause(self):
		self.onPlayPause = not self.onPlayPause

		self.drawPlayPause()
		self.win.refresh()
		
		if self.onPlayPause:
			time.sleep(self.highlightDuration)
			self.onPlayPause = False
			self.drawPlayPause()
			self.win.refresh()
		
	def pressStartRadio(self):
		self.onStartRadio = not self.onStartRadio

		self.drawStartRadio()
		self.win.refresh()
		
		if self.onStartRadio:
			time.sleep(self.highlightDuration)
			self.onStartRadio = False
			self.drawStartRadio()
			self.win.refresh()
		
def input_dummy():
	print("Test\n")
	time.sleep(2)

def input_light(stdscr):
	# Loop over time, waiting for key presses to trigger actions
	while True:
		# Get key
		k = stdscr.getch()

		if DBG:
			# Display the character pressed
			stdscr.addstr(25, hOffset, "Key pressed: <{}>                    ".format(k))
			stdscr.refresh()
			
		if k == ord('q'):
			# Quit application
			break

def input(stdscr, hOffset, zones, activeZoneIndex, globCtrls, zoneByName, DBG):
	# Loop over time, waiting for key presses to trigger actions
	while True:
		# Get key
		k = stdscr.getch()

		if DBG:
			# Display the character pressed
			stdscr.addstr(25, hOffset, "Key pressed: <{}>                    ".format(k))
			stdscr.refresh()
			
		if k == ord('q'):
			# Quit application
			break
		elif k == ord('m'):
			# Mute the current (active) zone
			zones[activeZoneIndex].toggleMute()
		elif k == ord('g'):
			# Toggle group membership of the current zone
			zones[activeZoneIndex].toggleInGroup()
		elif k == ord('d'):
			# Disable zone (testing purposes)
			zones[activeZoneIndex].disableZone()
		elif k == ord('e'):
			# Enable zone (testing purposes)
			zones[activeZoneIndex].enableZone()
		elif k == ord('p'):
			# Start or pause playback in the group
			globCtrls.pressPlayPause()
		elif k == ord('r'):
			# Group all zones, set volumes and play the preselected radio station
			zoneByName["Group"].resetParams(None, False)
			zoneByName["Kitchen"].resetParams(45, False, True)
			zoneByName["Living Room"].resetParams(40, False, True)
			zoneByName["Office"].resetParams(30, True, True)
			zoneByName["Bathroom"].resetParams(50, True, True)
			zoneByName["Bedroom"].resetParams(20, True, True)

			globCtrls.pressStartRadio()
		elif k == curses.KEY_UP or k == ord('+'):
			# Increase the volume for the current zone
			zones[activeZoneIndex].incrVolume()
		elif k == curses.KEY_DOWN or k == ord('-'):
			# Decrease the volume for the current zone
			zones[activeZoneIndex].decrVolume()
		elif k == ord("\t") or k == curses.KEY_RIGHT:
			# Cycle through zones
			zones[activeZoneIndex].toggleActive()
			activeZoneIndex += 1
			if activeZoneIndex >= len(zones):
				activeZoneIndex = 0
			zones[activeZoneIndex].toggleActive()
		elif k == curses.KEY_BTAB or curses.KEY_LEFT:
			# Cycle through zones (backwards)
			zones[activeZoneIndex].toggleActive()
			activeZoneIndex -= 1
			if activeZoneIndex < 0:
				activeZoneIndex = len(zones) - 1
			zones[activeZoneIndex].toggleActive()
		elif k == ord('h'):
			# Display help message !!! NOT WORKING !!!
			stdscr.addstr(27, hOffset, "Usage: ")
			stdscr.refresh()
	
class State:
	def __init__(self, state = True):
		self.state = state
		
	def isOn(self):
		return self.state
	
	def set(self, state):
		self.state = state
		
def output(zones, zoneByName, names, speakers, running):

	while running.isOn():
		# Test
		for zone in zones:
			zoneName = zone.zoneName
			
			try:
				volume = speakers[zoneName].volume
				
				zone.volume = volume
				zone.drawVolume()
				zone.win.refresh()
			except:
				pass
			
		time.sleep(5)


def main(stdscr):
	# Parameters
	DBG = True # Print debug statements
	title = "Poor man's Sonos Controller" # Application name
	# Size of each zone subwindow
	height = 10; 
	width = 15
	# Offset for the zone subwindows
	vOffset = 3
	hOffset = 2
	vPos = vOffset
	hPos = hOffset
	# Default volume to display
	volume = 50

	# Clear screen
	stdscr.clear()
	# Do no display the blinking cursor
	curses.curs_set(0)

	# Display the application title on the first line
	stdscr.addstr(0, hOffset, title, curses.A_UNDERLINE)

	# Create a zone for each zone, plus a group zone
	zoneNames = ["Group", "Kitchen", "Living Room", "Office", "Bathroom", "Bedroom"]
	zones = []
	zoneByName = {}

	for zoneName in zoneNames:
		zones.append(zone(stdscr, zoneName, height, width, vPos, hPos, volume, False, False))
		zoneByName[zoneName] = zones[-1]
		hPos += width

	# The first zone will be active at the beginning
	activeZoneIndex = 0
	zones[activeZoneIndex].toggleActive()


	# Global controls
	globCtrlsvOffset = vOffset + height
	globCtrlshOffset = hOffset
	globCtrlsHeight = 8
	globCtrlsWidth = 50

	globCtrls = globalControls(stdscr, globCtrlsHeight, globCtrlsWidth, globCtrlsvOffset, globCtrlshOffset)

	stdscr.refresh()

 	## Test
 	#k = stdscr.getch()
 	
 	# Prepare info about sonos speakers
 	import soco

	list_sonos = list(soco.discover())

	speakers = {}
	names = []

 	for speaker in list_sonos:
		name = speaker.get_speaker_info()['zone_name']
		names.append(name)
		speakers[name] = speaker
 	
 	# State indicator
 	running = State(True)
 	
	#inputThread = threading.Thread(name='input', target=input, args=(stdscr, hOffset, zones, activeZoneIndex, globCtrls, zoneByName, DBG))
	#inputThread = threading.Thread(name='input', target=input_light, args=(stdscr,))
	#inputThread = threading.Thread(name='input', target=input_dummy)
	outputThread = threading.Thread(name='output', target=output, args=(zones, zoneByName, names, speakers, running))

	#inputThread.start()
	outputThread.start()

	
	input(stdscr, hOffset, zones, activeZoneIndex, globCtrls, zoneByName, DBG)
	
	# Indicate that the program is stopping
	running.set(False)
	
# 	# Loop over time, waiting for key presses to trigger actions
# 	while True:
# 		# Get key
# 		k = stdscr.getch()
# 
# 		if DBG:
# 			# Display the character pressed
# 			stdscr.addstr(25, hOffset, "Key pressed: <{}>                    ".format(k))
# 			stdscr.refresh()
# 			
# 		if k == ord('q'):
# 			# Quit application
# 			break
# 		elif k == ord('m'):
# 			# Mute the current (active) zone
# 			zones[activeZoneIndex].toggleMute()
# 		elif k == ord('g'):
# 			# Toggle group membership of the current zone
# 			zones[activeZoneIndex].toggleInGroup()
# 		elif k == ord('d'):
# 			# Disable zone (testing purposes)
# 			zones[activeZoneIndex].disableZone()
# 		elif k == ord('e'):
# 			# Enable zone (testing purposes)
# 			zones[activeZoneIndex].enableZone()
# 		elif k == ord('p'):
# 			# Start or pause playback in the group
# 			globCtrls.pressPlayPause()
# 		elif k == ord('r'):
# 			# Group all zones, set volumes and play the preselected radio station
# 			zoneByName["Group"].resetParams(None, False)
# 			zoneByName["Kitchen"].resetParams(45, False, True)
# 			zoneByName["Living Room"].resetParams(40, False, True)
# 			zoneByName["Office"].resetParams(30, True, True)
# 			zoneByName["Bathroom"].resetParams(50, True, True)
# 			zoneByName["Bedroom"].resetParams(20, True, True)
# 
# 			globCtrls.pressStartRadio()
# 		elif k == curses.KEY_UP or k == ord('+'):
# 			# Increase the volume for the current zone
# 			zones[activeZoneIndex].incrVolume()
# 		elif k == curses.KEY_DOWN or k == ord('-'):
# 			# Decrease the volume for the current zone
# 			zones[activeZoneIndex].decrVolume()
# 		elif k == ord("\t") or k == curses.KEY_RIGHT:
# 			# Cycle through zones
# 			zones[activeZoneIndex].toggleActive()
# 			activeZoneIndex += 1
# 			if activeZoneIndex >= len(zones):
# 				activeZoneIndex = 0
# 			zones[activeZoneIndex].toggleActive()
# 		elif k == curses.KEY_BTAB or curses.KEY_LEFT:
# 			# Cycle through zones (backwards)
# 			zones[activeZoneIndex].toggleActive()
# 			activeZoneIndex -= 1
# 			if activeZoneIndex < 0:
# 				activeZoneIndex = len(zones) - 1
# 			zones[activeZoneIndex].toggleActive()
# 		elif k == ord('h'):
# 			# Display help message !!! NOT WORKING !!!
# 			stdscr.addstr(27, hOffset, "Usage: ")
# 			stdscr.refresh()


# Start the curses application
curses.wrapper(main)
