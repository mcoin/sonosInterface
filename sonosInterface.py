import curses
import time
import threading
from collections import OrderedDict
import soco
import logging
import os

from __builtin__ import True

class zone:
	def __init__ (self, parent, zoneName, height, width, y, x, volume, inGroup, mute, inGroupEnabled = True):
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

		self.drawWindow()

	def drawZoneName(self):
		self.win.addstr(self.vPosZoneName, self.hPosZoneName, self.zoneName, curses.A_STANDOUT if self.active else curses.A_NORMAL)

	def drawVolume(self):
		self.win.addstr(self.vPosVolume, self.hPosVolume, "Vol.: {:3d}".format(self.volume))

	def drawInGroup(self):
		string = "In group"
		if not self.inGroupEnabled:
			string = "        "	
		self.win.addstr(self.vPosInGroup, self.hPosInGroup, string, curses.A_BOLD if self.inGroup else curses.A_DIM)

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

		if self.reflectChangesDirectly:
			self.inGroup = not self.inGroup

			self.drawInGroup()
			self.win.refresh()
		else:
			self.triggerToggleInGroup = not self.triggerToggleInGroup

	def toggleMute(self):
		if not self.enabled:
			return

		if self.reflectChangesDirectly:
			self.mute = not self.mute
	
			self.drawMute()
			self.win.refresh()
		else:
			self.triggerToggleMute = not self.triggerToggleMute

	def toggleActive(self):
		self.active = not self.active

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
	
			self.drawVolume()
			self.win.refresh()
		else:
			self.triggerVolumeChange -= self.volDelta

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
			
	def setPrevNextZoneNames(self, prevZoneName, nextZoneName):
		self.prevZoneName = prevZoneName
		self.nextZoneName = nextZoneName
		
	def getPrevZoneName(self):
		return self.prevZoneName

	def getNextZoneName(self):
		return self.nextZoneName

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
						zone.drawVolume()
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
					zone.win.refresh()
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
					zone.volume = int(groupVolume)
					logging.debug("zone.volume = %f", zone.volume)
					zone.drawVolume()
					
					logging.debug("groupNbMute = %d", groupNbMute)
					zone.mute = groupNbMute == groupNbZones
					zone.drawMute()
				
				zone.win.refresh()
	
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


def sonosInterface(stdscr):
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
	volume = 50

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
		zones[zoneName] = zone(stdscr, zoneName, height, width, vPos, hPos, volume, False, False, inGroupEnabled)
		
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

	globCtrls = globalControls(stdscr, globCtrlsHeight, globCtrlsWidth, globCtrlsvOffset, globCtrlshOffset)

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
		logging.debug("Starting curses interface")
		interface(stdscr, hOffset, zones, activeZoneName, globCtrls, sleeperChange, DBG)
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
	# Start the curses application
	curses.wrapper(sonosInterface)