import curses
import time
import threading
from collections import OrderedDict
import soco
import logging
import os

from __builtin__ import True

class zone:
	def __init__ (self, parent, zoneName, height, width, y, x, volume, inGroup, mute, inGroupEnabled = True, cursesInterfaceActive = False):
		# Parameters
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.zoneName = zoneName
		self.volume = volume
		self.inGroup = inGroup
		self.mute = mute
		self.cursesInterfaceActive = cursesInterfaceActive
		if self.cursesInterfaceActive:
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
		self.maxVolume = 100
		self.inGroupEnabled = inGroupEnabled
		# Pointers to other zones
		self.prevZoneName = None
		self.nextZoneName = None
		# Triggers
		self.triggerToggleMute = False
		self.triggerToggleInGroup = False
		self.triggerVolumeChange = 0
		self.reflectChangesDirectly = False

		if self.cursesInterfaceActive:
			self.drawWindow()
		else:
			self.fo1=open("/tmp/c2s_fifo_2", "w")

	def printChanges(self, item, value, oldValue = 0):
		DBG = False
# 		map = {
# 			'Group': {'Mute': 'a', 'InGroup': 'b'},
# 			'Kitchen': {'Mute': 'c', 'InGroup': 'd'}
# 			}
		map = {
			'Mute': {
					'Group': 'l48', 
					'Kitchen': 'l49',
					'Living Room': 'l50',
					'Office': 'l51',
					'Bathroom': 'l52',
					'Bedroom': 'l53'
		},
			'InGroup': {
					'Kitchen': 'l55',
					'Living Room': 'l56',
					'Office': 'l57',
					'Bathroom': 'l58',
					'Bedroom': 'l59'
		},
			'Volume': {
					'Group': 'd0', 
					'Kitchen': 'd1',
					'Living Room': 'd2',
					'Office': 'd3',
					'Bathroom': 'd4',
					'Bedroom': 'd5'
		},
			}
			
		
		if self.cursesInterfaceActive:
			return
		
		try:
			# Treat state according to item kind
			if item == "Volume":
				suffix = str(int(value*255./100.)).zfill(3)
			else:
				suffix = str(1 if value else 0)
			codes = map[item][self.zoneName] + suffix
		except:
			codes = "?"
			
		if DBG:
			print("Zone name: %s - %s: %d [codes: '%s']" % (self.zoneName, item, value, codes))
		else:
			print codes
			#str = input("Message ?")
			self.fo1.write(codes)
			self.fo1.flush()
			
		
	def refresh(self):
		if self.cursesInterfaceActive:
			self.win.refresh()
		
	def drawZoneName(self):
		if self.cursesInterfaceActive:
			self.win.addstr(self.vPosZoneName, self.hPosZoneName, self.zoneName, curses.A_STANDOUT if self.active else curses.A_NORMAL)

	def drawVolume(self, oldValue = 0):
		self.printChanges("Volume", self.volume, oldValue)
		if self.cursesInterfaceActive:
			self.win.addstr(self.vPosVolume, self.hPosVolume, "Vol.: {:3d}".format(self.volume))

	def drawInGroup(self):
		self.printChanges("InGroup", self.inGroup)
		if not self.cursesInterfaceActive:
			return
		
		string = "In group"
		if not self.inGroupEnabled:
			string = "        "	
		self.win.addstr(self.vPosInGroup, self.hPosInGroup, string, curses.A_BOLD if self.inGroup else curses.A_DIM)

	def drawMute(self):
		self.printChanges("Mute", self.mute)
		if not self.cursesInterfaceActive:
			return
		
		self.win.addstr(self.vPosMute, self.hPosMute, "Mute", curses.A_BOLD if self.mute else curses.A_DIM)

	def drawWindow(self):
		if not self.cursesInterfaceActive:
			return
		
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

		if self.reflectChangesDirectly:
			self.inGroup = not self.inGroup

			if self.cursesInterfaceActive:
				self.drawInGroup()
				self.win.refresh()
		else:
			self.triggerToggleInGroup = not self.triggerToggleInGroup

	def toggleMute(self):
		#print("zone - toggleMute")
		if not self.enabled:
			return

		if self.reflectChangesDirectly:
			self.mute = not self.mute
	
			if self.cursesInterfaceActive:
				self.drawMute()
				self.win.refresh()
		else:
			self.triggerToggleMute = not self.triggerToggleMute

	def toggleActive(self):
		self.active = not self.active

		if self.cursesInterfaceActive:
			self.drawZoneName()
			self.win.refresh()

	def incrVolume(self):
		if not self.enabled:
			return

		if self.reflectChangesDirectly:
			prevVolume = self.volume
			self.volume += self.volDelta
			if self.volume > self.maxVolume:
				self.volume = self.maxVolume			
	
			if self.volume == prevVolume:
				return
	
			if self.cursesInterfaceActive:
				self.drawVolume()
				self.win.refresh()
		else:
			self.triggerVolumeChange += self.volDelta

	def decrVolume(self):
		if not self.enabled:
			return

		if self.reflectChangesDirectly:
			prevVolume = self.volume
			self.volume -= self.volDelta
			if self.volume < self.minVolume:
				self.volume = self.minVolume
	
			if self.volume == prevVolume:
				return
	
			if self.cursesInterfaceActive:
				self.drawVolume()
				self.win.refresh()
		else:
			self.triggerVolumeChange -= self.volDelta

	def disableZone(self):
		self.enabled = False
		if self.cursesInterfaceActive:
			self.win.bkgd('/')
			self.drawWindow()

	def enableZone(self):
		self.enabled = True
		if self.cursesInterfaceActive:
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

		if redraw and self.cursesInterfaceActive:
			self.drawWindow()
			
	def setPrevNextZoneNames(self, prevZoneName, nextZoneName):
		self.prevZoneName = prevZoneName
		self.nextZoneName = nextZoneName
		
	def getPrevZoneName(self):
		return self.prevZoneName

	def getNextZoneName(self):
		return self.nextZoneName

class globalControls:
	def __init__(self, parent, height, width, y, x, cursesInterfaceActive = False):
		# Parameters
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.cursesInterfaceActive = cursesInterfaceActive
		if self.cursesInterfaceActive:
			self.win = parent.subwin(self.height, self.width, self.y, self.x)
			self.win.box()
			# UI details
			self.vOffset = 2
			self.hOffset = 2
		# Usability parameters
		self.highlightDuration = 0.3 # seconds

		self.onPlayPause = False
		self.onStartRadio= False
		
		if self.cursesInterfaceActive:
			self.drawWindow()

	def drawPlayPause(self):
		if self.cursesInterfaceActive:
			self.win.addstr(self.vPosPlayPause, self.hPosPlayPause, "Play/Pause", curses.A_STANDOUT if self.onPlayPause else curses.A_NORMAL)

	def drawStartRadio(self):
		if self.cursesInterfaceActive:
			self.win.addstr(self.vPosStartRadio, self.hPosStartRadio, "Start Radio", curses.A_STANDOUT if self.onStartRadio else curses.A_NORMAL)

	def drawWindow(self):
		if not self.cursesInterfaceActive:
			return
		
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
		if self.cursesInterfaceActive:
			self.win.refresh()
		
		if self.onPlayPause:
			time.sleep(self.highlightDuration)
			self.onPlayPause = False
			if self.cursesInterfaceActive:
				self.drawPlayPause()
				self.win.refresh()
		
	def pressStartRadio(self):
		self.onStartRadio = not self.onStartRadio

		if self.cursesInterfaceActive:
			self.drawStartRadio()
			self.win.refresh()
		
		if self.onStartRadio:
			time.sleep(self.highlightDuration)
			self.onStartRadio = False
			if self.cursesInterfaceActive:
				self.drawStartRadio()
				self.win.refresh()
	
       
def getch():
	"""Gets a single character from standard input.  Does not echo to the
screen."""
	import sys, tty, termios
	old_settings = termios.tcgetattr(0)
	new_settings = old_settings[:]
	new_settings[3] &= ~termios.ICANON
	try:
		termios.tcsetattr(0, termios.TCSANOW, new_settings)
		ch = sys.stdin.read(1)
	finally:
		termios.tcsetattr(0, termios.TCSANOW, old_settings)
	return ch

def textInterface(zones, activeZoneName, globCtrls, sleeperChange):
	# Loop over time, waiting for key presses to be converted into actions
	map = {
		'19': ('Group', 'mute'),
		'23': ('Kitchen', 'mute'),
		'27': ('Living Room', 'mute'),
		'31': ('Office', 'mute'),
		'35': ('Bathroom', 'mute'),
		'f': ('Bedroom', 'mute'),
# 		'?': ('Group', 'inGroup'),
		'21': ('Kitchen', 'inGroup'),
		'25': ('Living Room', 'inGroup'),
		'29': ('Office', 'inGroup'),
		'33': ('Bathroom', 'inGroup'),
		'37': ('Bedroom', 'inGroup'), # Additional switches: 41, 43, 45, 47
		'0': ('Group', 'incrVol'),
		'2': ('Kitchen', 'incrVol'),
		'4': ('Living Room', 'incrVol'),
		'6': ('Office', 'incrVol'),
		'8': ('Bathroom', 'incrVol'),
		'10': ('Bedroom', 'incrVol'),
		'1': ('Group', 'decrVol'),
		'3': ('Kitchen', 'decrVol'),
		'5': ('Living Room', 'decrVol'),
		'7': ('Office', 'decrVol'),
		'9': ('Bathroom', 'decrVol'),
		'11': ('Bedroom', 'decrVol')
		}
	DBG = False
	
	while True:
		k = raw_input()
# 		k = getch()
				
		if DBG:
			print("key pressed: ", k)
		
		sendChanges = False
		if (k == 'Q'):
			break
		
		try:
			for code, action in map.iteritems():
				if k == code:
					if DBG:
						print("Executing action %s for zone %s" % (action[1], action[0]))
					zone = zones[action[0]]
					if action[1] == 'mute':
						zone.toggleMute()
						sendChanges = True
					if action[1] == 'group':
						zone.toggleInGroup()
						sendChanges = True
					if action[1] == 'incrVol':
						zone.incrVolume()
						sendChanges = True
					if action[1] == 'decrVol':
						zone.decrVolume()
						sendChanges = True
					break
		except:
			raise
		
		if sendChanges:
			with sleeperChange:
				sleeperChange.notifyAll()


       
       
def interface(stdscr, hOffset, zones, activeZoneName, globCtrls, sleeperChange, DBG):
	# Loop over time, waiting for key presses to trigger actions
	while True:
		# Flag used to send changes immediately
		sendChanges = False
		
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
			zones[activeZoneName].toggleMute()
			sendChanges = True
		elif k == ord('g'):
			# Toggle group membership of the current zone
			zones[activeZoneName].toggleInGroup()
			sendChanges = True
		elif k == ord('d'):
			# Disable zone (testing purposes)
			zones[activeZoneName].disableZone()
			sendChanges = True
		elif k == ord('e'):
			# Enable zone (testing purposes)
			zones[activeZoneName].enableZone()
			sendChanges = True
		elif k == ord('p'):
			# Start or pause playback in the group
			globCtrls.pressPlayPause()
			sendChanges = True
		elif k == ord('r'):
			# Group all zones, set volumes and play the preselected radio station
			zones["Group"].resetParams(None, False)
			zones["Kitchen"].resetParams(45, False, True)
			zones["Living Room"].resetParams(40, False, True)
			zones["Office"].resetParams(30, True, True)
			zones["Bathroom"].resetParams(50, True, True)
			zones["Bedroom"].resetParams(20, True, True)

			globCtrls.pressStartRadio()
			sendChanges = True
		elif k == curses.KEY_UP or k == ord('+'):
			# Increase the volume for the current zone
			zones[activeZoneName].incrVolume()
			sendChanges = True
		elif k == curses.KEY_DOWN or k == ord('-'):
			# Decrease the volume for the current zone
			zones[activeZoneName].decrVolume()
			sendChanges = True
		elif k == ord('h'):
			# Display help message !!! NOT WORKING !!!
			stdscr.addstr(27, hOffset, "Usage: ")
			stdscr.refresh()
# 			stdscr.addstr(27, hOffset, "               ")
		elif k == ord("\t") or k == curses.KEY_RIGHT:
			# Cycle through zones
			zones[activeZoneName].toggleActive()
			activeZoneName = zones[activeZoneName].getNextZoneName()
			zones[activeZoneName].toggleActive()
			sendChanges = True
		elif k == curses.KEY_BTAB or curses.KEY_LEFT:
			# Cycle through zones (backwards)
			zones[activeZoneName].toggleActive()
			activeZoneName = zones[activeZoneName].getPrevZoneName()
			zones[activeZoneName].toggleActive()
			sendChanges = True

		if sendChanges:
			with sleeperChange:
				sleeperChange.notifyAll()

class readSonosValues(threading.Thread):
	def __init__(self, zones, speakers, stopper, sleeperRead):
		super(readSonosValues, self).__init__()
		self.zones = zones
		self.speakers = speakers
		self.stopper = stopper
		self.sleeperRead = sleeperRead
		
	def run(self):
		init = True
		speakers = self.speakers
		zones = self.zones
		
		while not self.stopper.is_set():
			groupVolume = 0
			groupNbZones = 0
			groupNbMute = 0
			groupChanges = False
			if init:
				groupChanges = True
				init = False
			groupDef = None
			try:
				groupDef = speakers['Kitchen'].group.members
			except:
				raise
	
			logging.debug("Reading zone properties")
			for zoneName, zone in zones.items():
				logging.debug("  zone: %s", zoneName)
				# Treat group zone separately (if it exists)
				if zoneName == 'Group':
					continue
				
				refreshZone = False
	
				try:
					origInGroup = zone.inGroup
					inGroup = len(groupDef) > 1 and speakers[zoneName] in groupDef
					logging.debug("  zone: %s", zoneName)
					if inGroup != origInGroup:
						zone.inGroup = inGroup
						zone.drawInGroup()
						refreshZone = True
					if inGroup:
						groupNbZones += 1
				except:
					raise
	
				try:
					origVolume = zone.volume
					volume = speakers[zoneName].volume
					if volume != origVolume:
						zone.volume = volume
						zone.drawVolume(origVolume)
						refreshZone = True
					if zone.inGroup:
						logging.debug("Calculating total volume in group zone; zone = %s (zone.volume = %f)", zoneName, zone.volume)
						logging.debug("groupVolume = %f", groupVolume)
						groupVolume += volume
						logging.debug("groupVolume = %f", groupVolume)
				except:
					raise
				
				try:
					origMute = zone.mute
					mute = speakers[zoneName].mute
					if mute != origMute:
						zone.mute = mute
						zone.drawMute()
						refreshZone = True
					if zone.inGroup and mute:
						groupNbMute += 1
				except:
					raise
				
				if refreshZone:
					zone.refresh()
					groupChanges = True
					
			#for zoneName, zone in zones.items():
			
			# Group zone
			zone = zones['Group']
			logging.debug("Reading properties for group zone; groupChanges = %d", groupChanges)
			if groupChanges:
	 			if groupNbZones == 0 and zone.enabled:
	  				zone.disableZone()
	 			elif groupNbZones > 0 and not zone.enabled:
	 				zone.enableZone()
				
				logging.debug("groupNbZones = %d", groupNbZones)
				if groupNbZones > 0:
					logging.debug("groupVolume = %f", groupVolume)
					groupVolume = float(groupVolume)/float(groupNbZones)
					logging.debug("zone.volume = %f", zone.volume)
					origVolume = zone.volume
					zone.volume = int(groupVolume)
					logging.debug("zone.volume = %f", zone.volume)
					zone.drawVolume(origVolume)
					
					logging.debug("groupNbMute = %d", groupNbMute)
					zone.mute = groupNbMute == groupNbZones
					zone.drawMute()
				
				zone.refresh()
	
	# 		time.sleep(5)
#  			time.sleep(1)
 			with self.sleeperRead:
 				self.sleeperRead.wait(timeout = 5)
			

class changeSonosValues(threading.Thread):
	def __init__(self, zones, speakers, stopper, sleeperChange, sleeperRead):
		super(changeSonosValues, self).__init__()
		self.zones = zones
		self.speakers = speakers
		self.stopper = stopper
		self.sleeperRead = sleeperRead
		self.sleeperChange = sleeperChange
		
	def run(self):
		speakers = self.speakers
		zones = self.zones
				
		while not self.stopper.is_set():
			changes = False
			groupDef = None
			try:
				groupDef = speakers['Kitchen'].group.members
			except:
				raise
			
			for zoneName, zone in zones.items():
				# Treat group zone separately (if it exists)
				if zoneName == 'Group':
					continue
				
				refreshZone = False
	
				if zone.triggerToggleInGroup:
					changes = True
					if zone.inGroup:
						speakers[zoneName].unjoin()
					else:
						if zoneName != 'Kitchen':
							speakers[zoneName].join(speakers['Kitchen'])
						
					zone.triggerToggleInGroup = False
					
				if zone.triggerToggleMute:
					changes = True
					if zone.mute:
						speakers[zoneName].mute = False
					else:
						speakers[zoneName].mute = True
						
					zone.triggerToggleMute = False
					
				if zone.triggerVolumeChange != 0:
					changes = True
					speakers[zoneName].volume += zone.triggerVolumeChange
					
					zone.triggerVolumeChange = 0
					
			#for zoneName, zone in zones.items():
	
			# Group zone
			zone = zones['Group']
			if len(groupDef) > 1:
				groupMembers = set()
				for member in groupDef:
					groupMembers.add(member.player_name)
					
				logging.debug("Setting properties for group zone; zone.triggerToggleMute = %d", zone.triggerToggleMute)
				if zone.triggerToggleMute:
					changes = True
					zone.triggerToggleMute = False
					try:
						allMute = True
						for zoneName in zones:
							if zoneName in groupMembers:
								allMute = allMute and speakers[zoneName].mute
								
						for zoneName, zone in zones.items():
							if zoneName in groupMembers:
								speakers[zoneName].mute = not allMute
					except:
						raise
					
				logging.debug("Setting properties for group zone; zone.triggerVolumeChange = %d", zone.triggerVolumeChange)	
				if zone.triggerVolumeChange != 0:
					changes = True
					volumeChange = zone.triggerVolumeChange
					zone.triggerVolumeChange = 0
					logging.debug("Changing volume for group zone")
					try:
						for zoneName in zones:
							logging.debug("Changing volume for group zone: zone %s", zoneName)
							if zoneName in groupMembers:
								logging.debug("Changing volume for group zone: vol. += %f", volumeChange)
								speakers[zoneName].volume += volumeChange
					except:
						raise
					logging.debug("Changing volume for group zone: Setting volume change back to 0")
					
			# Changes occurred: Tell the reading thread to update immediately
			if changes:
				with self.sleeperRead:
					self.sleeperRead.notifyAll()
				
	# 		time.sleep(5)
# 			time.sleep(1)
			with self.sleeperChange:
				self.sleeperChange.wait(timeout = 5)


def sonosInterface(stdscr, cursesInterfaceActive = True):
	# Configure logging
	try:
		os.remove('sonosInterface.log')
	except OSError:
		pass
	logging.basicConfig(filename='sonosInterface.log',level=logging.DEBUG)
	logging.getLogger("requests").setLevel(logging.WARNING)
	logging.getLogger("soco").setLevel(logging.WARNING)
	
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
	volume = 0
	# Select an interface: Curses or Text
	textInterfaceActive = True
	if cursesInterfaceActive:
		textInterfaceActive = False

		# Clear screen
		stdscr.clear()
		# Do no display the blinking cursor
		curses.curs_set(0)

		# Display the application title on the first line
		stdscr.addstr(0, hOffset, title, curses.A_UNDERLINE)

	# Create a zone for each zone, plus a group zone
	zoneNames = ["Group", "Kitchen", "Living Room", "Office", "Bathroom", "Bedroom"]
	zones = OrderedDict()

	zoneNameIndex = 0 
	for zoneName in zoneNames:
		# Hide the "In group" parameter for the group zone
		inGroupEnabled = True if zoneName != "Group" else False
		zones[zoneName] = zone(stdscr, zoneName, height, width, vPos, hPos, volume, False, False, inGroupEnabled, cursesInterfaceActive)
		
		prevZoneNameIndex = zoneNameIndex - 1
		nextZoneNameIndex = zoneNameIndex + 1 if zoneNameIndex < len(zoneNames) - 1 else zoneNameIndex + 1 - len(zoneNames)
		
		zones[zoneName].setPrevNextZoneNames(zoneNames[prevZoneNameIndex], zoneNames[nextZoneNameIndex])
		hPos += width
		zoneNameIndex += 1

	# The first zone will be active at the beginning
	activeZoneName = zoneNames[0]
	zones[activeZoneName].toggleActive()
	
	# Global controls
	globCtrlsvOffset = vOffset + height
	globCtrlshOffset = hOffset
	globCtrlsHeight = 8
	globCtrlsWidth = 50

	globCtrls = globalControls(stdscr, globCtrlsHeight, globCtrlsWidth, globCtrlsvOffset, globCtrlshOffset, cursesInterfaceActive)

	if cursesInterfaceActive:
		stdscr.refresh()

 	
 	# Prepare info about sonos speakers
	list_sonos = list(soco.discover())

	speakers = {}
	names = []

 	for speaker in list_sonos:
		name = speaker.get_speaker_info()['zone_name']
		names.append(name)
		speakers[name] = speaker
 	
 	# State indicator
	stopper = threading.Event()
	 		 
	# Timer for threads
	sleeperRead = threading.Condition()
	sleeperChange = threading.Condition()
	
	#inputThread = threading.Thread(name='input', target=input, args=(stdscr, hOffset, zones, activeZoneNameIndex, globCtrls, zoneByName, DBG))
# 	readSonosValuesThread = threading.Thread(name='readSonosValues', target=readSonosValues, args=(zones, speakers, running))
	readSonosValuesThread = readSonosValues(zones, speakers, stopper, sleeperRead)
# 	changeSonosValuesThread = threading.Thread(name='changeSonosValues', target=changeSonosValues, args=(zones, speakers, running))
	changeSonosValuesThread = changeSonosValues(zones, speakers, stopper, sleeperChange, sleeperRead)

	
	#inputThread.start()
	logging.debug("Starting readSonosValuesThread thread")
 	readSonosValuesThread.start()
	logging.debug("Starting changeSonosValuesThread thread")
 	changeSonosValuesThread.start()

	try:
		if cursesInterfaceActive:
			logging.debug("Starting curses interface")
			interface(stdscr, hOffset, zones, activeZoneName, globCtrls, sleeperChange, DBG)
		if textInterfaceActive:
			logging.debug("Starting text interface")
			textInterface(zones, activeZoneName, globCtrls, sleeperChange)
	except:
		pass
	finally:
		# Indicate that the program is stopping so that the slave process also stops
		stopper.set()
		# Cancel timers in the threads
		with sleeperRead:
			sleeperRead.notifyAll()
		with sleeperChange:
			sleeperChange.notifyAll()


if __name__ == '__main__':
	
	cursesInterfaceActive = False
	
	if cursesInterfaceActive:
		# Start the curses application
		curses.wrapper(sonosInterface)
	else:
		# Start the text-based interface
		dummy = 0
		sonosInterface(dummy, False)